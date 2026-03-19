from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import razorpay
import hmac
import hashlib
from app.database import get_db
from app.models.models import Worker, Policy, PolicyStatus, PolicyTier
from app.schemas.schemas import PolicyCreate, PolicyResponse, PremiumQuote, PolicyOrderResponse, PolicyPaymentVerify
from app.services.auth_service import get_current_worker
from app.services.premium_service import calculate_premium, BASE_PREMIUMS, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT
from app.config import settings

router = APIRouter()


def _razorpay_client():
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@router.post("/create-order", response_model=PolicyOrderResponse)
async def create_order(
    payload: PolicyCreate,
    current_worker: Worker = Depends(get_current_worker),
):
    """Create a Razorpay order for policy payment"""
    pincode = payload.pincode or current_worker.pincode
    premium_data = calculate_premium(tier=payload.tier, pincode=pincode)
    amount_paise = int(premium_data["adjusted_premium"] * 100)

    client = _razorpay_client()
    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1,
        "notes": {
            "worker_id": current_worker.id,
            "tier": payload.tier.value,
        }
    })

    return PolicyOrderResponse(
        order_id=order["id"],
        amount=amount_paise,
        currency="INR",
        tier=payload.tier.value,
        adjusted_premium=premium_data["adjusted_premium"],
        key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post("/verify-payment", response_model=PolicyResponse)
async def verify_payment(
    payload: PolicyPaymentVerify,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Verify Razorpay payment signature and activate policy"""
    # Verify signature
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected != payload.razorpay_signature:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Check no active policy exists
    existing = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
            Policy.end_date >= datetime.utcnow(),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Active policy already exists")

    pincode = payload.pincode or current_worker.pincode
    premium_data = calculate_premium(tier=payload.tier, pincode=pincode)

    now = datetime.utcnow()
    policy = Policy(
        worker_id=current_worker.id,
        tier=payload.tier,
        status=PolicyStatus.ACTIVE,
        weekly_premium=premium_data["adjusted_premium"],
        base_premium=premium_data["base_premium"],
        max_daily_payout=premium_data["max_daily_payout"],
        max_weekly_payout=premium_data["max_weekly_payout"],
        pincode=pincode,
        city=current_worker.city,
        start_date=now,
        end_date=now + timedelta(days=7),
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.get("/quote", response_model=PremiumQuote)
async def get_quote(
    tier: PolicyTier = PolicyTier.SMART,
    current_worker: Worker = Depends(get_current_worker),
):
    """Get premium quote for a given tier"""
    result = calculate_premium(
        tier=tier,
        pincode=current_worker.pincode,
        worker_history_factor=1.0,
        platform_activity_score=1.0,
    )
    return PremiumQuote(**result)


@router.post("/", response_model=PolicyResponse)
async def create_policy(
    payload: PolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    """Create a new weekly policy"""
    # Check no active policy exists
    existing = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
            Policy.end_date >= datetime.utcnow(),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Active policy already exists for this week")

    pincode = payload.pincode or current_worker.pincode
    premium_data = calculate_premium(tier=payload.tier, pincode=pincode)

    now = datetime.utcnow()
    policy = Policy(
        worker_id=current_worker.id,
        tier=payload.tier,
        status=PolicyStatus.ACTIVE,
        weekly_premium=premium_data["adjusted_premium"],
        base_premium=premium_data["base_premium"],
        max_daily_payout=premium_data["max_daily_payout"],
        max_weekly_payout=premium_data["max_weekly_payout"],
        pincode=pincode,
        city=current_worker.city,
        start_date=now,
        end_date=now + timedelta(days=7),
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.get("/", response_model=list[PolicyResponse])
async def list_policies(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    result = await db.execute(
        select(Policy)
        .where(Policy.worker_id == current_worker.id)
        .order_by(Policy.created_at.desc())
    )
    return result.scalars().all()


@router.get("/active", response_model=PolicyResponse)
async def get_active_policy(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
            Policy.end_date >= datetime.utcnow(),
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="No active policy found")
    return policy
