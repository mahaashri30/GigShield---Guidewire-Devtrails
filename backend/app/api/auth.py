from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Worker
from app.schemas.schemas import OTPRequest, OTPVerify, TokenResponse
from app.services.auth_service import generate_otp, verify_otp, create_access_token, create_refresh_token

router = APIRouter()


@router.post("/send-otp")
async def send_otp(payload: OTPRequest):
    """Send OTP to worker's phone number"""
    otp = generate_otp(payload.phone)
    # In production: send via MSG91 / Fast2SMS
    return {
        "message": "OTP sent successfully",
        "phone": payload.phone,
        # Remove in production - only for dev
        "dev_otp": otp if True else None,
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp_endpoint(payload: OTPVerify, db: AsyncSession = Depends(get_db)):
    """Verify OTP and return JWT tokens"""
    if not verify_otp(payload.phone, payload.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    result = await db.execute(select(Worker).where(Worker.phone == payload.phone))
    worker = result.scalar_one_or_none()
    is_new = worker is None

    if is_new:
        # Create placeholder worker - full profile in /workers/register
        worker = Worker(phone=payload.phone, name="", platform="zomato", city="", pincode="")
        db.add(worker)
        await db.commit()
        await db.refresh(worker)

    access_token = create_access_token({"sub": worker.id, "phone": worker.phone})
    refresh_token = create_refresh_token({"sub": worker.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        worker_id=worker.id,
        is_new_user=is_new,
    )
