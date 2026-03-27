from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, Payout, PolicyStatus, ClaimStatus, PayoutStatus
from app.schemas.schemas import ClaimResponse
from app.services.auth_service import get_current_worker
from app.services.premium_service import calculate_payout, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT
from app.services.fraud_service import calculate_fraud_score
from app.services.payout_service import initiate_upi_payout

router = APIRouter()


@router.post("/trigger/{disruption_event_id}", response_model=ClaimResponse)
async def trigger_claim(
    disruption_event_id: str,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    now = datetime.now(timezone.utc)

    # Get active policy
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
        ).order_by(Policy.created_at.desc())
    )
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=400, detail="No active policy found")
    # Handle timezone-naive end_date from DB
    end_date = policy.end_date
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    if end_date < now:
        policy.status = PolicyStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Policy has expired")

    # Get disruption event
    result = await db.execute(select(DisruptionEvent).where(DisruptionEvent.id == disruption_event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Disruption event not found")

    if event.city.lower() != current_worker.city.lower():
        raise HTTPException(status_code=400, detail="Disruption event is not in your city")

    # Duplicate claim check
    dup = await db.execute(
        select(Claim).where(
            Claim.worker_id == current_worker.id,
            Claim.disruption_event_id == disruption_event_id,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already claimed this disruption event")

    # Claims this week (for fraud scoring)
    week_ago = now - timedelta(days=7)
    count_result = await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == current_worker.id,
            Claim.created_at >= week_ago,
        )
    )
    claims_this_week = count_result.scalar() or 0

    # Fraud detection
    event_started_at = event.started_at
    if event_started_at.tzinfo is None:
        event_started_at = event_started_at.replace(tzinfo=timezone.utc)
    fraud_result = calculate_fraud_score(
        worker_city=current_worker.city,
        event_city=event.city,
        worker_pincode=current_worker.pincode,
        event_pincode=event.pincode or "",
        was_platform_active=True,
        claims_this_week=claims_this_week,
        claims_same_event=0,
        event_started_at=event_started_at,
        claim_created_at=now,
    )

    # Weekly cap remaining = tier weekly cap - total already claimed this policy week
    weekly_cap     = MAX_WEEKLY_PAYOUT[policy.tier]
    weekly_claimed = float(policy.total_claimed or 0)
    weekly_remaining = max(0.0, weekly_cap - weekly_claimed)

    if weekly_remaining <= 0:
        raise HTTPException(status_code=400, detail="Weekly payout cap reached for this policy")

    # Daily cap remaining
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.coalesce(func.sum(Claim.approved_amount), 0.0)).where(
            Claim.worker_id == current_worker.id,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
            Claim.created_at >= today_start,
        )
    )
    claimed_today = float(today_result.scalar() or 0)

    # Effective cap = min(daily remaining, weekly remaining)
    daily_cap       = MAX_DAILY_PAYOUT[policy.tier]
    daily_remaining = max(0.0, daily_cap - claimed_today)
    effective_cap   = min(daily_remaining, weekly_remaining)

    # Payout = income shortfall, capped at effective_cap
    payout_data = calculate_payout(
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=event.dss_multiplier,
        active_hours_ratio=1.0,
        tier=policy.tier,
        existing_claimed_today=daily_cap - effective_cap,  # pass what's already used
    )

    claim = Claim(
        worker_id=current_worker.id,
        policy_id=policy.id,
        disruption_event_id=event.id,
        status=ClaimStatus.PENDING,
        claimed_amount=payout_data["raw_payout"],
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=event.dss_multiplier,
        active_hours_ratio=1.0,
        fraud_score=fraud_result["fraud_score"],
        fraud_flags=fraud_result["flags_json"],
        auto_approved=fraud_result["auto_approve"],
    )

    if fraud_result["auto_approve"]:
        approved = min(payout_data["income_shortfall"], effective_cap)
        claim.status = ClaimStatus.APPROVED
        claim.approved_amount = round(approved, 2)
        claim.processed_at = now
        policy.total_claimed = round(weekly_claimed + approved, 2)
        policy.claims_count += 1

    elif fraud_result["auto_reject"]:
        claim.status = ClaimStatus.REJECTED
        claim.rejection_reason = "; ".join(fraud_result["flags"])
        claim.processed_at = now

    db.add(claim)
    await db.commit()
    await db.refresh(claim)

    # Auto-payout if approved and amount > 0
    if claim.status == ClaimStatus.APPROVED and (claim.approved_amount or 0) > 0:
        upi_id = current_worker.upi_id or f"worker_{current_worker.id[:8]}@upi"
        payout_result = await initiate_upi_payout(
            worker_id=current_worker.id,
            upi_id=upi_id,
            amount=claim.approved_amount,
            claim_id=claim.id,
        )
        payout = Payout(
            claim_id=claim.id,
            worker_id=current_worker.id,
            amount=claim.approved_amount,
            upi_id=upi_id,
            status=PayoutStatus.COMPLETED if payout_result["success"] else PayoutStatus.FAILED,
            razorpay_payout_id=payout_result.get("payout_id"),
            transaction_ref=payout_result.get("transaction_ref"),
            completed_at=now if payout_result["success"] else None,
        )
        if payout_result["success"]:
            claim.status = ClaimStatus.PAID
        db.add(payout)
        await db.commit()
        await db.refresh(claim)

    return claim


@router.get("/", response_model=list[ClaimResponse])
async def list_claims(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    result = await db.execute(
        select(Claim)
        .where(Claim.worker_id == current_worker.id)
        .order_by(Claim.created_at.desc())
    )
    return result.scalars().all()
