"""
Phase 5: Admin Dashboard - Loss Ratio Analytics

Implements:
- Daily aggregation of loss-ratio metrics (premiums vs payouts)
- By tier and geography (pincode)
- Materialized view for fast admin dashboard queries
- Calculates: loss ratio, claim approval rate, average payout per claim
"""
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.models import (
    Policy, Claim, Payout, ClaimStatus, PayoutStatus, PolicyTier,
    LossRatioDashboard, PolicyStatus
)


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)


@celery_app.task(name="app.workers.loss_ratio_worker.aggregate_loss_ratio_metrics")
def aggregate_loss_ratio_metrics():
    """
    Celery task: Run daily (e.g., at midnight IST) to aggregate loss-ratio metrics.
    
    Aggregates:
    - Premiums collected
    - Claims submitted, approved, rejected, paid
    - Payouts made
    - Loss ratio = payouts / premiums
    - Approval rate = approved / submitted
    
    By:
    - Tier (BASIC, SMART, PRO)
    - Geography (pincode_6digit or NULL for all)
    """
    return _run(_aggregate_loss_ratio_metrics_async())


async def _aggregate_loss_ratio_metrics_async():
    """Async implementation of loss-ratio aggregation."""
    db: AsyncSession = AsyncSessionLocal()
    
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get all active policies as of today
        policies_result = await db.execute(
            select(Policy).where(
                and_(
                    Policy.status == PolicyStatus.ACTIVE,
                    Policy.start_date <= now,
                    Policy.end_date >= today_start,
                )
            )
        )
        all_policies = policies_result.scalars().all()
        
        # Group by tier and pincode_6digit
        aggregations = {}  # (tier, pincode_6digit) -> data
        
        for policy in all_policies:
            key = (policy.tier, policy.pincode_6digit)
            if key not in aggregations:
                aggregations[key] = {
                    "tier": policy.tier,
                    "pincode_6digit": policy.pincode_6digit,
                    "pincode_3digit_zone": policy.pincode_3digit_zone,
                    "city": policy.city,
                    "policies_active": 0,
                    "premiums_collected": 0.0,
                    "claims_submitted": 0,
                    "claims_approved": 0,
                    "claims_rejected": 0,
                    "claims_paid": 0,
                    "payouts_made": 0.0,
                }
            
            aggregations[key]["policies_active"] += 1
            aggregations[key]["premiums_collected"] += policy.weekly_premium
        
        # Get all claims from today
        claims_result = await db.execute(
            select(Claim).where(
                Claim.created_at >= today_start
            )
        )
        today_claims = claims_result.scalars().all()
        
        # Map claims to aggregations by their policy's tier and pincode
        for claim in today_claims:
            policy_result = await db.execute(
                select(Policy).where(Policy.id == claim.policy_id)
            )
            policy = policy_result.scalar_one_or_none()
            if not policy:
                continue
            
            key = (policy.tier, policy.pincode_6digit)
            if key not in aggregations:
                # Policy might not be in active set, create entry
                aggregations[key] = {
                    "tier": policy.tier,
                    "pincode_6digit": policy.pincode_6digit,
                    "pincode_3digit_zone": policy.pincode_3digit_zone,
                    "city": policy.city,
                    "policies_active": 0,
                    "premiums_collected": 0.0,
                    "claims_submitted": 0,
                    "claims_approved": 0,
                    "claims_rejected": 0,
                    "claims_paid": 0,
                    "payouts_made": 0.0,
                }
            
            aggregations[key]["claims_submitted"] += 1
            
            if claim.status == ClaimStatus.APPROVED:
                aggregations[key]["claims_approved"] += 1
            elif claim.status == ClaimStatus.REJECTED:
                aggregations[key]["claims_rejected"] += 1
            elif claim.status == ClaimStatus.PAID:
                aggregations[key]["claims_paid"] += 1
            
            # Add payout amount if paid
            if claim.payout:
                aggregations[key]["payouts_made"] += claim.payout.amount
        
        # Create or update LossRatioDashboard entries
        for (tier, pincode_6digit), data in aggregations.items():
            # Calculate derived metrics
            loss_ratio = (
                data["payouts_made"] / data["premiums_collected"]
                if data["premiums_collected"] > 0 else None
            )
            approval_rate = (
                data["claims_approved"] / data["claims_submitted"]
                if data["claims_submitted"] > 0 else None
            )
            avg_premium = (
                data["premiums_collected"] / data["policies_active"]
                if data["policies_active"] > 0 else None
            )
            avg_payout_per_claim = (
                data["payouts_made"] / data["claims_paid"]
                if data["claims_paid"] > 0 else None
            )
            
            # Check if entry already exists for today
            existing_result = await db.execute(
                select(LossRatioDashboard).where(
                    and_(
                        func.DATE(LossRatioDashboard.aggregation_date) == today_start.date(),
                        LossRatioDashboard.tier == tier,
                        LossRatioDashboard.pincode_6digit == pincode_6digit,
                    )
                )
            )
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                # Update
                existing.policies_active = data["policies_active"]
                existing.premiums_collected = data["premiums_collected"]
                existing.claims_submitted = data["claims_submitted"]
                existing.claims_approved = data["claims_approved"]
                existing.claims_rejected = data["claims_rejected"]
                existing.claims_paid = data["claims_paid"]
                existing.payouts_made = data["payouts_made"]
                existing.loss_ratio = loss_ratio
                existing.approval_rate = approval_rate
                existing.avg_premium_per_worker = avg_premium
                existing.avg_payout_per_claim = avg_payout_per_claim
            else:
                # Create
                dashboard_entry = LossRatioDashboard(
                    aggregation_date=today_start,
                    tier=tier,
                    pincode_6digit=pincode_6digit,
                    pincode_3digit_zone=data.get("pincode_3digit_zone"),
                    city=data.get("city"),
                    policies_active=data["policies_active"],
                    premiums_collected=data["premiums_collected"],
                    claims_submitted=data["claims_submitted"],
                    claims_approved=data["claims_approved"],
                    claims_rejected=data["claims_rejected"],
                    claims_paid=data["claims_paid"],
                    payouts_made=data["payouts_made"],
                    loss_ratio=loss_ratio,
                    claim_approval_rate=approval_rate,
                    avg_premium_per_worker=avg_premium,
                    avg_payout_per_claim=avg_payout_per_claim,
                )
                db.add(dashboard_entry)
        
        # Also create a system-wide rollup (tier + NULL pincode = all pincodes)
        for tier in PolicyTier:
            tier_data = {
                "policies_active": 0,
                "premiums_collected": 0.0,
                "claims_submitted": 0,
                "claims_approved": 0,
                "claims_rejected": 0,
                "claims_paid": 0,
                "payouts_made": 0.0,
            }
            
            for (t, pcode), data in aggregations.items():
                if t == tier:
                    for key in tier_data:
                        tier_data[key] += data[key]
            
            # Calculate rollup metrics
            loss_ratio = (
                tier_data["payouts_made"] / tier_data["premiums_collected"]
                if tier_data["premiums_collected"] > 0 else None
            )
            approval_rate = (
                tier_data["claims_approved"] / tier_data["claims_submitted"]
                if tier_data["claims_submitted"] > 0 else None
            )
            
            # Check if exists
            rollup_result = await db.execute(
                select(LossRatioDashboard).where(
                    and_(
                        func.DATE(LossRatioDashboard.aggregation_date) == today_start.date(),
                        LossRatioDashboard.tier == tier,
                        LossRatioDashboard.pincode_6digit.is_(None),
                    )
                )
            )
            existing_rollup = rollup_result.scalar_one_or_none()
            
            if existing_rollup:
                existing_rollup.policies_active = tier_data["policies_active"]
                existing_rollup.premiums_collected = tier_data["premiums_collected"]
                existing_rollup.claims_submitted = tier_data["claims_submitted"]
                existing_rollup.claims_approved = tier_data["claims_approved"]
                existing_rollup.claims_rejected = tier_data["claims_rejected"]
                existing_rollup.claims_paid = tier_data["claims_paid"]
                existing_rollup.payouts_made = tier_data["payouts_made"]
                existing_rollup.loss_ratio = loss_ratio
                existing_rollup.claim_approval_rate = approval_rate
            else:
                rollup_entry = LossRatioDashboard(
                    aggregation_date=today_start,
                    tier=tier,
                    pincode_6digit=None,
                    city=None,
                    policies_active=tier_data["policies_active"],
                    premiums_collected=tier_data["premiums_collected"],
                    claims_submitted=tier_data["claims_submitted"],
                    claims_approved=tier_data["claims_approved"],
                    claims_rejected=tier_data["claims_rejected"],
                    claims_paid=tier_data["claims_paid"],
                    payouts_made=tier_data["payouts_made"],
                    loss_ratio=loss_ratio,
                    claim_approval_rate=approval_rate,
                )
                db.add(rollup_entry)
        
        await db.commit()
        return {
            "status": "success",
            "aggregations_created": len(aggregations),
            "timestamp": now.isoformat(),
        }
        
    except Exception as e:
        await db.rollback()
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        await db.close()
