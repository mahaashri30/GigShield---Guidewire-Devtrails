from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, PolicyStatus
from app.schemas.schemas import WorkerCreate, WorkerUpdate, WorkerResponse, WorkerDashboard
from app.services.auth_service import get_current_worker

router = APIRouter()


@router.post("/register", response_model=WorkerResponse)
async def register_worker(
    payload: WorkerCreate,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Complete worker registration after OTP verification"""
    current_worker.name = payload.name
    current_worker.platform = payload.platform
    current_worker.city = payload.city
    current_worker.pincode = payload.pincode
    current_worker.upi_id = payload.upi_id
    current_worker.platform_worker_id = payload.platform_worker_id
    current_worker.is_verified = True
    await db.commit()
    await db.refresh(current_worker)
    return current_worker


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


@router.get("/dashboard", response_model=WorkerDashboard)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Get worker dashboard data"""
    from datetime import datetime

    # Active policy
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
            Policy.end_date >= datetime.utcnow(),
        )
    )
    active_policy = result.scalar_one_or_none()

    # Recent claims (last 5)
    result = await db.execute(
        select(Claim)
        .where(Claim.worker_id == current_worker.id)
        .order_by(Claim.created_at.desc())
        .limit(5)
    )
    recent_claims = result.scalars().all()

    # Total earned protection (sum of approved payouts)
    total_protection = sum(
        c.approved_amount or 0 for c in recent_claims if c.approved_amount
    )

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
