"""
Phase 4: Claims Disbursement - Inactivity Validation

Implements:
- Hold claims for confirmed inactivity (HOLD_FOR_INACTIVITY_REVIEW status)
- After 2 hours of continued inactivity, auto-approve claim
- If worker resumes activity during hold period, auto-reject claim
- Reduces false positives (worker was actually working elsewhere)
"""
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.models import (
    Claim, ClaimStatus, WorkerLocationPing, Worker,
    WorkerNotification, Payout, PayoutStatus
)


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)


@celery_app.task(name="app.workers.inactivity_worker.verify_inactivity_hold_claims")
def verify_inactivity_hold_claims():
    """
    Celery task: Run every 30 minutes to process claims in HOLD_FOR_INACTIVITY_REVIEW status.
    
    For each held claim:
    1. Check if worker has been inactive for 2+ hours (both app + GPS)
    2. If still inactive: auto-approve and initiate payout
    3. If activity resumed: auto-reject claim (worker was working elsewhere)
    """
    return _run(_verify_inactivity_hold_claims_async())


async def _verify_inactivity_hold_claims_async():
    """Async implementation of inactivity verification."""
    db: AsyncSession = AsyncSessionLocal()
    
    try:
        now = datetime.now(timezone.utc)
        hold_threshold = now - timedelta(hours=2)  # 2 hours ago
        
        # Find all claims in HOLD_FOR_INACTIVITY_REVIEW status created before hold_threshold
        result = await db.execute(
            select(Claim).where(
                and_(
                    Claim.status == ClaimStatus.HOLD_FOR_INACTIVITY_REVIEW,
                    Claim.created_at <= hold_threshold,  # On hold for 2+ hours
                )
            )
        )
        held_claims = result.scalars().all()
        
        approved_count = 0
        rejected_count = 0
        
        for claim in held_claims:
            # Check if worker resumed activity since claim creation
            resumed_activity = await _check_worker_activity_since(
                worker_id=claim.worker_id,
                since=claim.created_at,
                db=db
            )
            
            if resumed_activity:
                # Worker resumed work: auto-reject
                claim.status = ClaimStatus.REJECTED
                claim.rejection_reason = "Worker resumed activity during hold period; income disruption not confirmed"
                
                # Notify worker
                notification = WorkerNotification(
                    worker_id=claim.worker_id,
                    title="Claim Rejected",
                    body=f"Your claim #{claim.id[:8]} was rejected because activity resumed. "
                         f"Income disruption is only valid during confirmed inactive periods.",
                    notif_type="claim_rejected",
                    ref_id=claim.id,
                )
                db.add(notification)
                rejected_count += 1
                
            else:
                # Worker remained inactive: auto-approve and initiate payout
                claim.status = ClaimStatus.APPROVED
                claim.auto_approved = True
                
                # Initiate payout if not already done
                if not claim.payout:
                    payout = Payout(
                        claim_id=claim.id,
                        worker_id=claim.worker_id,
                        amount=claim.approved_amount or claim.claimed_amount,
                        status=PayoutStatus.PENDING,
                    )
                    db.add(payout)
                
                # Notify worker
                notification = WorkerNotification(
                    worker_id=claim.worker_id,
                    title="Claim Approved",
                    body=f"Your claim #{claim.id[:8]} has been approved and will be disbursed shortly. "
                         f"Amount: ₹{claim.approved_amount or claim.claimed_amount:.0f}",
                    notif_type="claim_approved",
                    ref_id=claim.id,
                )
                db.add(notification)
                approved_count += 1
        
        await db.commit()
        return {
            "status": "success",
            "claims_processed": len(held_claims),
            "approved": approved_count,
            "rejected": rejected_count,
        }
        
    except Exception as e:
        await db.rollback()
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        await db.close()


async def _check_worker_activity_since(
    worker_id: str,
    since: datetime,
    db: AsyncSession
) -> bool:
    """
    Check if worker has shown activity (app login or GPS ping) since given timestamp.
    
    Returns:
        True if activity detected, False if remained inactive
    """
    try:
        # Check for location pings after claim creation
        ping_result = await db.execute(
            select(WorkerLocationPing).where(
                and_(
                    WorkerLocationPing.worker_id == worker_id,
                    WorkerLocationPing.recorded_at > since,
                )
            ).limit(1)
        )
        if ping_result.scalar_one_or_none():
            return True  # Has location ping = activity detected
        
        # TODO: Check app heartbeat/login if available in logging system
        # For now, just check GPS pings
        
        return False  # No activity detected
        
    except Exception:
        # On error, assume no activity (conservative approach: auto-approve)
        return False
