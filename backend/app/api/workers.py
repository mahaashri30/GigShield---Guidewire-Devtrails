from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, PolicyStatus
from app.schemas.schemas import WorkerCreate, WorkerUpdate, WorkerResponse, WorkerDashboard
from app.services.auth_service import get_current_worker
from app.services.platform_service import fetch_platform_earnings
from datetime import datetime, timezone

router = APIRouter()


@router.post("/register", response_model=WorkerResponse)
async def register_worker(
    payload: WorkerCreate,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Complete worker registration — auto-fetches avg earnings from platform API"""
    current_worker.name = payload.name
    current_worker.platform = payload.platform
    current_worker.city = payload.city
    current_worker.pincode = payload.pincode
    current_worker.upi_id = payload.upi_id
    current_worker.platform_worker_id = payload.platform_worker_id

    # Auto-fetch avg daily earnings from platform using worker's phone number
    earnings_data = await fetch_platform_earnings(
        phone=current_worker.phone,
        platform=payload.platform.value,
        city=payload.city,
    )
    current_worker.avg_daily_earnings = earnings_data["avg_daily_earnings"]
    current_worker.avg_online_hours_per_day = earnings_data.get("avg_online_hours_per_day", 9.0)
    current_worker.avg_orders_per_day = earnings_data.get("avg_orders_per_day", 18.0)
    current_worker.active_days_30 = earnings_data.get("active_days_30", 0)

    # Override with worker self-reported values if provided
    if payload.avg_online_hours_per_day:
        current_worker.avg_online_hours_per_day = payload.avg_online_hours_per_day
    if payload.avg_orders_per_day:
        current_worker.avg_orders_per_day = payload.avg_orders_per_day

    # Underwriting rule: minimum 7 active delivery days before cover eligibility
    current_worker.is_verified = current_worker.active_days_30 >= 7
    await db.commit()
    await db.refresh(current_worker)
    return current_worker


@router.get("/platform-earnings", response_model=dict)
async def get_platform_earnings(
    platform: str,
    current_worker: Worker = Depends(get_current_worker),
):
    """Fetch earnings data from the worker's platform using their phone number.
    Called during onboarding to show the worker what earnings were detected."""
    return await fetch_platform_earnings(
        phone=current_worker.phone,
        platform=platform,
    )


@router.delete("/me")
async def delete_account(
    payload: dict = None,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """
    Production-level account deletion — 4-step process:

    Step 1 — Archive: Snapshot PII + financial summary into deleted_account_archives.
    Step 2 — Hard delete non-financial data: GPS pings, notifications, FCM token,
              device fingerprint, SIM hash (no business value, pure PII).
    Step 3 — Anonymise PII on worker row: name, phone, UPI, bank details wiped.
              Financial records (claims, policies, payouts) are KEPT but detached
              from PII — required for IRDAI 5-year actuarial/audit retention.
    Step 4 — Soft delete: is_deleted=True, is_active=False.
              A scheduled job purges the anonymised worker row after 30 days.

    The worker can re-register with the same phone after 30 days.
    """
    import hashlib
    from datetime import timedelta
    from sqlalchemy import delete as sql_delete, func
    from app.models.models import (
        WorkerLocationPing, WorkerNotification,
        DeletedAccountArchive, ClaimStatus,
    )

    now = datetime.now(timezone.utc)
    worker_id = current_worker.id
    reason = (payload or {}).get("reason", "") if payload else ""

    # ── Step 1: Build financial summary for archive ───────────────────────────
    policy_count_result = await db.execute(
        select(func.count(Policy.id)).where(Policy.worker_id == worker_id)
    )
    total_policies = policy_count_result.scalar() or 0

    claim_count_result = await db.execute(
        select(func.count(Claim.id)).where(Claim.worker_id == worker_id)
    )
    total_claims = claim_count_result.scalar() or 0

    premium_result = await db.execute(
        select(func.coalesce(func.sum(Policy.weekly_premium), 0.0))
        .where(Policy.worker_id == worker_id)
    )
    total_premium = float(premium_result.scalar() or 0)

    claims_paid_result = await db.execute(
        select(func.coalesce(func.sum(Claim.approved_amount), 0.0))
        .where(
            Claim.worker_id == worker_id,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
        )
    )
    total_claims_paid = float(claims_paid_result.scalar() or 0)

    # Phone hash — used to block re-registration during grace period
    phone_hash = hashlib.sha256(current_worker.phone.encode()).hexdigest()
    name_redacted = (current_worker.name[:2] + "***") if current_worker.name else "***"

    archive = DeletedAccountArchive(
        original_worker_id=worker_id,
        phone_hash=phone_hash,
        name_redacted=name_redacted,
        city=current_worker.city,
        platform=current_worker.platform.value if current_worker.platform else None,
        total_policies=total_policies,
        total_claims=total_claims,
        total_premium_paid=total_premium,
        total_claims_paid=total_claims_paid,
        deletion_requested_at=now,
        deletion_reason=reason[:200] if reason else None,
        grace_period_ends_at=now + timedelta(days=30),
    )
    db.add(archive)
    await db.flush()

    # ── Step 2: Hard delete non-financial / pure PII data ─────────────────────
    await db.execute(
        sql_delete(WorkerNotification).where(WorkerNotification.worker_id == worker_id)
    )
    await db.execute(
        sql_delete(WorkerLocationPing).where(WorkerLocationPing.worker_id == worker_id)
    )

    # ── Step 3: Anonymise PII on worker row ───────────────────────────────────
    # Financial records (Policy, Claim, Payout) are intentionally KEPT.
    # They reference worker_id (a UUID) not the phone/name — so they are
    # already pseudonymised once the PII fields below are wiped.
    current_worker.name             = "[DELETED]"
    current_worker.phone            = f"del_{worker_id[:8]}"
    current_worker.upi_id           = None
    current_worker.bank_account     = None
    current_worker.bank_ifsc        = None
    current_worker.aadhaar_last4    = None
    current_worker.fcm_token        = None
    current_worker.device_fingerprint = None
    current_worker.sim_hash         = None
    current_worker.last_known_lat   = None
    current_worker.last_known_lng   = None
    current_worker.last_location_at = None
    current_worker.email            = None

    # ── Step 4: Soft delete ───────────────────────────────────────────────────
    current_worker.is_deleted             = True
    current_worker.is_active              = False
    current_worker.is_verified            = False
    current_worker.deletion_requested_at  = now

    # Cancel any active policies
    active_policies_result = await db.execute(
        select(Policy).where(
            Policy.worker_id == worker_id,
            Policy.status == PolicyStatus.ACTIVE,
        )
    )
    for p in active_policies_result.scalars().all():
        p.status = PolicyStatus.CANCELLED
        p.end_date = now

    await db.commit()

    return {
        "message": "Account deletion requested. Your data will be permanently purged after 30 days.",
        "grace_period_ends": (now + timedelta(days=30)).isoformat(),
        "financial_records_retained": "Claims and payout records are retained for 5 years as required by IRDAI regulations.",
    }


@router.get("/me", response_model=WorkerResponse)
async def get_me(current_worker: Worker = Depends(get_current_worker)):
    return current_worker


@router.patch("/me", response_model=WorkerResponse)
async def update_me(
    payload: WorkerUpdate,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_worker, field, value)
    await db.commit()
    await db.refresh(current_worker)
    return current_worker


@router.post("/fcm-token")
async def register_fcm_token(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Register or refresh FCM push token for this device."""
    token = payload.get("fcm_token", "").strip()
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="fcm_token is required")
    current_worker.fcm_token = token
    await db.commit()
    return {"ok": True}


@router.post("/device-fingerprint")
async def register_device_fingerprint(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """
    Called on every app launch. Stores device fingerprint and detects changes.
    If fingerprint changed since registration, sets sim_changed_at so the
    fraud/eligibility engine can flag claims from this worker for review.
    """
    from datetime import datetime, timezone
    fingerprint = payload.get("fingerprint", "").strip()
    changed = payload.get("changed", False)

    if not fingerprint:
        return {"ok": True}

    if current_worker.device_fingerprint is None:
        # First registration — store it
        current_worker.device_fingerprint = fingerprint
    elif changed and current_worker.device_fingerprint != fingerprint:
        # Device changed — flag it for fraud engine
        current_worker.sim_changed_at = datetime.now(timezone.utc)
        current_worker.device_fingerprint = fingerprint

    await db.commit()
    return {"ok": True, "changed": changed}


@router.get("/dashboard", response_model=WorkerDashboard)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Get worker dashboard data"""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
        ).order_by(Policy.created_at.desc())
    )
    all_policies = result.scalars().all()
    active_policy = None
    for p in all_policies:
        end = p.end_date.replace(tzinfo=timezone.utc) if p.end_date.tzinfo is None else p.end_date
        if end >= now:
            active_policy = p
            break

    # Recent claims (last 5)
    result = await db.execute(
        select(Claim)
        .where(Claim.worker_id == current_worker.id)
        .order_by(Claim.created_at.desc())
        .limit(5)
    )
    recent_claims = result.scalars().all()

    # Total earned protection (sum of all approved/paid payouts, not just last 5)
    from sqlalchemy import func
    from app.models.models import ClaimStatus
    total_result = await db.execute(
        select(func.coalesce(func.sum(Claim.approved_amount), 0.0)).where(
            Claim.worker_id == current_worker.id,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
        )
    )
    total_protection = float(total_result.scalar() or 0)

    # Active disruptions in worker's city
    result = await db.execute(
        select(DisruptionEvent).where(
            DisruptionEvent.city == current_worker.city,
            DisruptionEvent.is_active == True,
        )
    )
    active_disruptions = result.scalars().all()

    return WorkerDashboard(
        worker=current_worker,
        active_policy=active_policy,
        recent_claims=recent_claims,
        total_earned_protection=total_protection,
        active_disruptions=active_disruptions,
    )
