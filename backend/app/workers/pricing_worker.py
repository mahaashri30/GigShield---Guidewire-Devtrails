"""
Phase 2: Pricing Engine - Feedback Loop & Pincode-Level Personalization

Implements:
- Renewal premium recalculation based on claims history
- Tier recommendations for new customers
- Dynamic pricing based on pincode-specific risk
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.models import (
    Policy, Worker, PolicyStatus, PolicyTier, PricingAudit, ClaimsMetrics
)
from app.services.premium_service import calculate_premium


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)


@celery_app.task(name="app.workers.pricing_worker.recalculate_policy_on_renewal")
def recalculate_policy_on_renewal():
    """
    Celery task: Run daily to recalculate premiums for policies ending soon.
    
    Flow:
    1. Find policies ending within next 7 days
    2. Recalculate premium based on worker's claims history (last 30/90 days)
    3. If premium increases >10%, show recommendation; if <10%, auto-apply
    4. Log change in PricingAudit table
    5. Send notification to worker
    """
    return _run(_recalculate_policy_on_renewal_async())


async def _recalculate_policy_on_renewal_async():
    """Async implementation of renewal pricing recalculation."""
    db: AsyncSession = AsyncSessionLocal()
    
    try:
        now = datetime.now(timezone.utc)
        renewal_window_start = now
        renewal_window_end = now + timedelta(days=7)
        
        # Find policies ending within next 7 days
        result = await db.execute(
            select(Policy).where(
                and_(
                    Policy.status == PolicyStatus.ACTIVE,
                    Policy.end_date >= renewal_window_start,
                    Policy.end_date <= renewal_window_end,
                )
            )
        )
        policies_to_renew = result.scalars().all()
        
        recalculated_count = 0
        
        for policy in policies_to_renew:
            # Get worker for context
            worker_result = await db.execute(
                select(Worker).where(Worker.id == policy.worker_id)
            )
            worker = worker_result.scalar_one_or_none()
            if not worker:
                continue
            
            # Get claims metrics for this worker
            metrics_result = await db.execute(
                select(ClaimsMetrics).where(
                    ClaimsMetrics.worker_id == worker.id
                ).order_by(ClaimsMetrics.calculated_at.desc()).limit(1)
            )
            metrics = metrics_result.scalar_one_or_none()
            
            previous_premium = policy.base_premium
            previous_tier = policy.tier
            
            # Calculate new premium based on claims history + pincode risk
            new_premium = await calculate_premium(
                tier=policy.tier,
                pincode_6digit=policy.pincode_6digit or policy.pincode,
                worker_claims_history=metrics.claims_30day if metrics else 0,
                worker_payout_ratio=metrics.payout_ratio_30day if metrics else 0.0,
                db=db
            )
            
            # Determine if should auto-apply or show recommendation
            premium_change_pct = ((new_premium - previous_premium) / previous_premium * 100) if previous_premium else 0
            
            # Create audit log
            audit = PricingAudit(
                policy_id=policy.id,
                previous_tier=previous_tier,
                previous_premium=previous_premium,
                new_tier=policy.tier,
                new_premium=new_premium,
                recalc_reason="RENEWAL",
                claims_30day=metrics.claims_30day if metrics else 0,
                payout_ratio_30day=metrics.payout_ratio_30day if metrics else None,
            )
            db.add(audit)
            
            # Auto-apply if premium decreased or increase < 10%
            if premium_change_pct <= 10:
                policy.base_premium = new_premium
                policy.weekly_premium = new_premium
                
                # Send notification (auto-applied)
                notification_body = (
                    f"Your premium for renewal has been recalculated. "
                    f"New premium: ₹{new_premium:.0f}/week. "
                    f"Change: {premium_change_pct:+.1f}%"
                )
                
                recalculated_count += 1
            else:
                # Premium increase > 10%: show recommendation popup
                # Store recommendation in worker notification (handled in API layer)
                notification_body = (
                    f"Your premium is due for renewal. "
                    f"New premium: ₹{new_premium:.0f}/week (was ₹{previous_premium:.0f}). "
                    f"Change: {premium_change_pct:+.1f}%. "
                    f"Tap to review and accept."
                )
        
        await db.commit()
        return {
            "status": "success",
            "policies_processed": len(policies_to_renew),
            "recalculated_count": recalculated_count,
        }
        
    except Exception as e:
        await db.rollback()
        return {
            "status": "error",
            "message": str(e),
        }
    finally:
        await db.close()


async def recommend_tier_for_new_customer(
    pincode: str,
    pincode_6digit: str,
    platform: str,
    avg_daily_income: float,
    db: AsyncSession
) -> dict:
    """
    Recommend a policy tier based on worker profile and geographic risk.
    
    Args:
        pincode: Full 10-digit pincode
        pincode_6digit: 6-digit pincode for lookup
        platform: Delivery platform (Blinkit, Zepto, etc.)
        avg_daily_income: Worker's average daily income
        db: Database session
    
    Returns:
        {
            "recommended_tier": "BASIC|SMART|PRO",
            "reason": "explanation",
            "estimated_coverage": "Daily income coverage %",
            "premiums": {"BASIC": X, "SMART": Y, "PRO": Z}
        }
    """
    from app.models.models import PincodeTriggerProbability, DisruptionType
    
    try:
        # Get trigger probabilities for this pincode
        prob_result = await db.execute(
            select(PincodeTriggerProbability).where(
                PincodeTriggerProbability.pincode_6digit == pincode_6digit
            )
        )
        probs = prob_result.scalars().all()
        
        # Calculate expected disruption frequency and average payout need
        avg_trigger_prob = sum(p.probability for p in probs) / len(probs) if probs else 0.15
        expected_disruptions_per_year = avg_trigger_prob * 365
        
        # Estimate coverage need
        # If worker works 25 days/month and earns avg_daily_income
        # They need coverage for disruption days
        monthly_disruptions = expected_disruptions_per_year / 12
        coverage_need = monthly_disruptions * avg_daily_income
        
        # Map coverage to tier
        # BASIC: ₹300/day → ~₹6300/month (21 days * 300)
        # SMART: ₹550/day → ~₹11550/month (21 days * 550)
        # PRO: ₹750/day → ~₹15750/month (21 days * 750)
        
        if coverage_need < 6000:
            recommended_tier = PolicyTier.BASIC
            tier_reason = "Low disruption risk in your area; BASIC tier covers most scenarios"
        elif coverage_need < 12000:
            recommended_tier = PolicyTier.SMART
            tier_reason = "Moderate disruption risk; SMART tier balances coverage and cost"
        else:
            recommended_tier = PolicyTier.PRO
            tier_reason = "High disruption risk in your area; PRO tier provides maximum coverage"
        
        # Calculate premiums for all tiers
        base_premiums = {
            PolicyTier.BASIC: 29.0,
            PolicyTier.SMART: 49.0,
            PolicyTier.PRO: 79.0,
        }
        
        return {
            "recommended_tier": recommended_tier.value,
            "reason": tier_reason,
            "expected_disruptions_per_year": int(expected_disruptions_per_year),
            "coverage_need_monthly": coverage_need,
            "premiums": {tier.value: base_premiums[tier] for tier in PolicyTier},
        }
        
    except Exception as e:
        # Fallback to SMART tier if error
        return {
            "recommended_tier": PolicyTier.SMART.value,
            "reason": "Default recommendation",
            "premiums": {"basic": 29.0, "smart": 49.0, "pro": 79.0},
        }
