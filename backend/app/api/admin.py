from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.delete("/clear-test-data")
async def clear_test_data(db: AsyncSession = Depends(get_db)):
    """Clear all test data — resets DB for fresh demo."""
    await db.execute(text("TRUNCATE TABLE payouts, claims, policies, disruption_events, workers CASCADE"))
    await db.commit()
    return {"message": "All test data cleared. DB is fresh for demo."}
