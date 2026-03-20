from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, Payout, PolicyStatus, ClaimStatus, PayoutStatus
from app.schemas.schemas import ClaimResponse
from app.services.auth_service import get_current_worker
from app.services.premium_service import calculate_payout
from app.services.fraud_service import calculate_fraud_score
from app.services.payout_service import initiate_upi_payout

router = APIRouter()


@router.post("/trigger/{disruption_event_id}", response_model=ClaimResponse)
async def trigger_claim(
    disruption_event_id: str,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Manually trigger a claim for a disruption event (auto-triggered by Celery in prod)"""
    # Get active policy
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
            Policy.end_date >= datetime.now(timezone.utc),
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=400, detail="No active policy found")

    # Get disruption event
    result = await db.execute(select(DisruptionEvent).where(DisruptionEvent.id == disruption_event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Disruption event not found")

    if event.city.lower() != current_worker.city.lower():
        raise HTTPException(status_code=400, detail="Disruption event is not in your city")

    # Check for duplicate claim
    dup_result = await db.execute(
        select(Claim).where(
            Claim.worker_id == current_worker.id,
            Claim.disruption_event_id == disruption_event_id,
        )
    )
    if dup_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already claimed this disruption event")

    # Count claims this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
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
        was_platform_active=True,  # Mock: assume active
        claims_this_week=claims_this_week,
        claims_same_event=0,
        event_started_at=event.started_at,
        claim_created_at=datetime.now(timezone.utc),
    )

    # Calculate payout
    payout_data = calculate_payout(
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=event.dss_multiplier,
        active_hours_ratio=1.0,
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
        active_hours_ratio=1.0,
        fraud_score=fraud_result["fraud_score"],
        fraud_flags=fraud_result["flags_json"],
        auto_approved=fraud_result["auto_approve"],
    )

    if fraud_result["auto_approve"]:
        claim.status = ClaimStatus.APPROVED
        claim.approved_amount = payout_data["approved_amount"]
        claim.processed_at = datetime.now(timezone.utc)

        # Update policy totals
        policy.total_claimed += payout_data["approved_amount"]
        policy.claims_count += 1

    elif fraud_result["auto_reject"]:
        claim.status = ClaimStatus.REJECTED
        claim.rejection_reason = "; ".join(fraud_result["flags"])
        claim.processed_at = datetime.now(timezone.utc)

    db.add(claim)
    await db.commit()
    await db.refresh(claim)

    # Auto-payout if approved
    upi_id = current_worker.upi_id or f"worker_{current_worker.id[:8]}@upi"
    if claim.status == ClaimStatus.APPROVED:
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
            completed_at=datetime.now(timezone.utc) if payout_result["success"] else None,
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
