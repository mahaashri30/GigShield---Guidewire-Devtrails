from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, Payout, PolicyStatus, ClaimStatus, PayoutStatus, DisruptionType
from app.schemas.schemas import ClaimResponse
from app.services.auth_service import get_current_worker
from app.services.premium_service import calculate_payout, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT
from app.services.fraud_service import calculate_fraud_score
from app.services.payout_service import initiate_upi_payout

router = APIRouter()

# City pools — which disruption types are valid per city
# Delhi/NCR: AQI + Heat pool | Mumbai/Bangalore: Rain pool | All: Civic + Traffic
CITY_POOLS = {
    "Delhi":     [DisruptionType.AQI_SPIKE, DisruptionType.EXTREME_HEAT, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Mumbai":    [DisruptionType.HEAVY_RAIN, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Bangalore": [DisruptionType.HEAVY_RAIN, DisruptionType.AQI_SPIKE, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Chennai":   [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Hyderabad": [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
}

# Active hours: delivery workers operate 6am-10pm IST
ACTIVE_HOUR_START = 6
ACTIVE_HOUR_END = 22


def is_within_active_hours(dt: datetime) -> bool:
    """Check if event occurred during worker active hours (6am-10pm IST)"""
    ist_hour = (dt.hour + 5) % 24  # UTC+5:30 approx
    return ACTIVE_HOUR_START <= ist_hour < ACTIVE_HOUR_END


def active_hours_ratio(event_started_at: datetime) -> float:
    """Returns ratio of remaining active hours after event start."""
    ist_hour = (event_started_at.hour + 5) % 24
    if ist_hour < ACTIVE_HOUR_START or ist_hour >= ACTIVE_HOUR_END:
        return 0.0  # Event outside active hours — no income loss
    remaining = ACTIVE_HOUR_END - ist_hour
    total_active = ACTIVE_HOUR_END - ACTIVE_HOUR_START
    return round(remaining / total_active, 2)


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

    # City pool check: trigger must be valid for worker's city pool
    allowed_types = CITY_POOLS.get(current_worker.city, list(DisruptionType))
    if event.disruption_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"{event.disruption_type} is not covered in {current_worker.city} pool")

    # Active hours check: trigger must be during worker's active hours (6am-10pm IST)
    event_started_at = event.started_at
    if event_started_at.tzinfo is None:
        event_started_at = event_started_at.replace(tzinfo=timezone.utc)
    hours_ratio = active_hours_ratio(event_started_at)
    if hours_ratio == 0.0:
        raise HTTPException(status_code=400, detail="Disruption occurred outside active delivery hours (6am-10pm)")

    # Ward-level check: pincode prefix must match (same zone, not just same city)
    worker_prefix = current_worker.pincode[:3] if current_worker.pincode else ""
    event_prefix = (event.pincode or "")[:3]
    if event_prefix and worker_prefix and worker_prefix != event_prefix:
        # Allow if within same city but different ward — reduce payout by 30%
        ward_mismatch = True
    else:
        ward_mismatch = False

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
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
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

    # Payout = income shortfall adjusted for active hours ratio and ward proximity
    effective_hours_ratio = hours_ratio * (0.7 if ward_mismatch else 1.0)
    payout_data = calculate_payout(
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=event.dss_multiplier,
        active_hours_ratio=effective_hours_ratio,
        tier=policy.tier,
    )

    claim = Claim(
        worker_id=current_worker.id,
        policy_id=policy.id,
        disruption_event_id=event.id,
        status=ClaimStatus.PENDING,
        claimed_amount=payout_data["raw_payout"],
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=event.dss_multiplier,
        active_hours_ratio=effective_hours_ratio,
        fraud_score=fraud_result["fraud_score"],
        fraud_flags=fraud_result["flags_json"],
        auto_approved=fraud_result["auto_approve"],
    )

    if fraud_result["auto_approve"]:
        income_shortfall = payout_data.get("income_shortfall") or payout_data.get("approved_amount") or payout_data.get("raw_payout") or 0.0
        approved = min(income_shortfall, effective_cap)
        claim.status = ClaimStatus.APPROVED
        claim.approved_amount = round(approved, 2)
        claim.processed_at = now
        policy.total_claimed = round(weekly_claimed + approved, 2)
        policy.claims_count = (policy.claims_count or 0) + 1

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
