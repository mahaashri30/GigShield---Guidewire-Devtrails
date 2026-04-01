from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import Worker, Policy, Claim, PolicyTier, ClaimStatus, PolicyStatus
from app.services.auth_service import get_current_worker
from app.services.actuarial_service import calculate_actuarial_premium, calculate_bcr, stress_test_monsoon

router = APIRouter()


@router.get("/premium-formula")
async def get_actuarial_premium(
    tier: PolicyTier = PolicyTier.SMART,
    current_worker: Worker = Depends(get_current_worker),
):
    """Actuarial base premium: P(trigger) × avg_income_lost × days_exposed"""
    return calculate_actuarial_premium(
        tier=tier,
        city=current_worker.city or "Bangalore",
        avg_daily_earnings=current_worker.avg_daily_earnings,
    )


@router.get("/bcr")
async def get_bcr(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """BCR = total claims paid / total premium collected. Target: 0.55-0.70"""
    claims_result = await db.execute(
        select(func.coalesce(func.sum(Claim.approved_amount), 0.0)).where(
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID])
        )
    )
    total_claims = float(claims_result.scalar() or 0)

    premium_result = await db.execute(
        select(func.coalesce(func.sum(Policy.weekly_premium), 0.0)).where(
            Policy.status.in_([PolicyStatus.ACTIVE, PolicyStatus.EXPIRED])
        )
    )
    total_premium = float(premium_result.scalar() or 0)

    return calculate_bcr(total_claims, total_premium)


@router.get("/stress-test")
async def get_stress_test(
    tier: PolicyTier = PolicyTier.SMART,
    current_worker: Worker = Depends(get_current_worker),
):
    """14-day monsoon stress scenario per worker."""
    return stress_test_monsoon(
        city=current_worker.city or "Bangalore",
        avg_daily_earnings=current_worker.avg_daily_earnings,
        tier=tier,
    )
