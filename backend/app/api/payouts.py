from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Payout, Worker
from app.schemas.schemas import PayoutResponse
from app.services.auth_service import get_current_worker

router = APIRouter()


@router.get("/", response_model=list[PayoutResponse])
async def list_payouts(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    result = await db.execute(
        select(Payout)
        .where(Payout.worker_id == current_worker.id)
        .order_by(Payout.initiated_at.desc())
    )
    return result.scalars().all()
