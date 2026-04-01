from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.models.models import DisruptionEvent, Worker
from app.schemas.schemas import DisruptionEventResponse
from app.services.auth_service import get_current_worker
from app.services.disruption_service import check_disruptions
from app.config import settings

router = APIRouter()


@router.get("/active", response_model=list[DisruptionEventResponse])
async def get_active_disruptions(
    city: str = Query(..., description="City name"),
    db: AsyncSession = Depends(get_db),
):
    """Get all active disruption events for a city"""
    result = await db.execute(
        select(DisruptionEvent).where(
            DisruptionEvent.city == city,
            DisruptionEvent.is_active == True,
        )
    )
    return result.scalars().all()


@router.post("/simulate", response_model=list[DisruptionEventResponse])
async def simulate_disruption(
    city: str = Query(...),
    pincode: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    if settings.ENVIRONMENT != "development":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Simulation only available in development mode")
    events_data = await check_disruptions(city=city, pincode=pincode)
    events = []

    for e in events_data:
        event = DisruptionEvent(
            disruption_type=e["disruption_type"],
            severity=e["severity"],
            city=e["city"],
            pincode=e["pincode"],
            dss_multiplier=e["dss_multiplier"],
            raw_value=e.get("raw_value"),
            description=e.get("description"),
            source=e.get("source"),
            started_at=datetime.utcnow(),
            is_active=True,
        )
        db.add(event)
        events.append(event)

    await db.commit()
    for e in events:
        await db.refresh(e)

    return events


@router.get("/", response_model=list[DisruptionEventResponse])
async def list_disruptions(
    city: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(DisruptionEvent).order_by(DisruptionEvent.created_at.desc()).limit(50)
    if city:
        query = query.where(DisruptionEvent.city == city)
    result = await db.execute(query)
    return result.scalars().all()
