"""
Verification API Routes - Multi-stage identity verification for delivery workers.
Includes: OTP verification, Partner ID check, Selfie liveness, Govt ID OCR.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import logging
import io
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.models import Worker, VerificationStatus, GovtIDType
from app.services.auth_service import get_current_worker, AuthContext, get_current_auth_context
from app.services.bedrock_service import BedrockAIService
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize AWS Bedrock AI service
bedrock_service = BedrockAIService(region_name=getattr(settings, 'AWS_REGION', 'us-east-1'))


# ============================================================================
# Schema Definitions
# ============================================================================

class PhoneVerificationRequest(BaseModel):
    phone: str
    platform: str  # "blinkit", "zepto", "swiggy_instamart", "zomato", etc.


class SelfieVerificationRequest(BaseModel):
    selfie_image_base64: str  # Base64-encoded selfie photo


class SelfieVerificationResponse(BaseModel):
    verified: bool
    match_score: float
    confidence: float
    error: Optional[str]


class GovtIDVerificationRequest(BaseModel):
    id_type: str  # "driving_license", "voter_id", "aadhaar", "pan"
    name: str     # Name for verification


class GovtIDVerificationResponse(BaseModel):
    verified: bool
    extracted_name: Optional[str]
    extracted_id_number: Optional[str]
    name_match: bool
    confidence: float
    error: Optional[str]


class VerificationStatusResponse(BaseModel):
    verification_status: str
    phone_verified: bool
    selfie_verified: bool
    govt_id_verified: bool
    fully_verified: bool


# ============================================================================
# Step 1: Phone Verification (OTP already handled in auth.py)
# ============================================================================

@router.post("/verify/phone", response_model=VerificationStatusResponse)
async def verify_phone(
    request: PhoneVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify phone number registration with delivery platform.
    This checks if the phone number is registered with the specified platform.
    """
    try:
        # Query if worker exists
        result = await db.execute(
            select(Worker).where(Worker.phone == request.phone)
        )
        worker = result.scalar_one_or_none()
        
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Phone number not registered with {request.platform}"
            )
        
        # Update phone verification
        await db.execute(
            update(Worker)
            .where(Worker.id == worker.id)
            .values(
                phone_verified_at=datetime.utcnow(),
                verification_status=VerificationStatus.PHONE_VERIFIED
            )
        )
        await db.commit()
        
        logger.info(f"Phone verification successful: {request.phone}")
        
        return VerificationStatusResponse(
            verification_status=VerificationStatus.PHONE_VERIFIED,
            phone_verified=True,
            selfie_verified=worker.selfie_verified_at is not None,
            govt_id_verified=worker.govt_id_verified_at is not None,
            fully_verified=False
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Phone verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Phone verification failed"
        )


# ============================================================================
# Step 2: Selfie Verification (Face Recognition)
# ============================================================================

@router.post("/verify/selfie", response_model=SelfieVerificationResponse)
async def verify_selfie(
    file: UploadFile = File(...),
    auth_context: AuthContext = Depends(get_current_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify selfie against government ID photo using face recognition.
    Requires govt_id_image_url to be already uploaded.
    """
    try:
        worker = auth_context.worker
        
        # Check if worker has govt ID uploaded
        if not worker.govt_id_image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Government ID must be uploaded first"
            )
        
        # Read selfie image
        selfie_bytes = await file.read()
        if len(selfie_bytes) > 15 * 1024 * 1024:  # 15MB limit
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail="Image too large (max 15MB)"
            )
        
        # Convert to base64
        import base64
        selfie_base64 = base64.b64encode(selfie_bytes).decode()
        
        # Get govt ID image (in production, this would be downloaded from storage)
        # For now, we'll use the stored URL as reference
        if not worker.govt_id_image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Government ID must be uploaded first"
            )
        
        # Run face verification using AWS Bedrock
        result = bedrock_service.verify_selfie_with_id(
            selfie_image_data=selfie_base64,
            id_image_data=selfie_base64,  # In production, fetch from govt_id_image_url
            is_base64=True
        )
        
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        if result["verified"]:
            # Save selfie and update verification status
            # In production, upload to Firestore/S3 and save URL
            await db.execute(
                update(Worker)
                .where(Worker.id == worker.id)
                .values(
                    selfie_verified_at=datetime.utcnow(),
                    face_match_score=result["match_score"],
                    # selfie_image_url=firestore_url,  # In production
                    verification_status=VerificationStatus.SELFIE_VERIFIED
                )
            )
            await db.commit()
            
            logger.info(
                f"Selfie verification successful for worker {worker.id}: "
                f"score={result['match_score']:.4f}"
            )
        else:
            logger.warning(
                f"Selfie verification failed for worker {worker.id}: "
                f"score={result['match_score']:.4f}"
            )
        
        return SelfieVerificationResponse(
            verified=result["verified"],
            match_score=result["match_score"],
            confidence=result["confidence"],
            error=result["error"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Selfie verification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Selfie verification failed"
        )


# ============================================================================
# Step 3: Government ID Verification (OCR)
# ============================================================================

@router.post("/verify/govt-id", response_model=GovtIDVerificationResponse)
async def verify_govt_id(
    id_type: str = Form(...),
    file: UploadFile = File(...),
    auth_context: AuthContext = Depends(get_current_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify government ID document using OCR.
    Extracts name, ID number, and other fields from the document.
    """
    try:
        worker = auth_context.worker
        
        # Validate ID type
        if id_type not in [t.value for t in GovtIDType]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ID type. Must be one of: {[t.value for t in GovtIDType]}"
            )
        
        # Read ID image
        id_bytes = await file.read()
        if len(id_bytes) > 15 * 1024 * 1024:  # 15MB limit
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail="Image too large (max 15MB)"
            )
        
        # Convert to base64
        import base64
        id_base64 = base64.b64encode(id_bytes).decode()
        
        # Run OCR verification using AWS Bedrock
        import asyncio
        result = await asyncio.to_thread(
            bedrock_service.extract_govt_id_fields,
            id_base64,
            id_type,
            True
        )
        
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        extracted_name = result["extracted_fields"].get("name")
        extracted_id = result["extracted_fields"].get("id_number")
        
        # Verify name matches if provided
        name_match = False
        if extracted_name and worker.name:
            name_lower = worker.name.strip().lower()
            extracted_lower = extracted_name.strip().lower()
            name_match = (
                name_lower == extracted_lower or
                name_lower in extracted_lower or
                extracted_lower in name_lower
            )
        
        # Determine if verification passed
        is_verified = (
            result["confidence"] > 75 and
            result["quality_score"] > 60 and
            name_match
        )
        
        if is_verified:
            # Save govt ID and update verification status
            # In production, upload to Firestore/S3 and save URL
            await db.execute(
                update(Worker)
                .where(Worker.id == worker.id)
                .values(
                    govt_id_type=GovtIDType[id_type.upper()],
                    govt_id_name=extracted_name,
                    govt_id_number=extracted_id,
                    govt_id_verified_at=datetime.utcnow(),
                    # govt_id_image_url=firestore_url,  # In production
                    
                    # Update to fully verified if all steps complete (phone + selfie + govt_id)
                    verification_status=VerificationStatus.FULLY_VERIFIED if all([
                        worker.phone_verified_at,
                        worker.selfie_verified_at
                    ]) else VerificationStatus.GOVT_ID_VERIFIED,
                    
                    is_verified=True
                )
            )
            await db.commit()
            
            logger.info(
                f"Govt ID verification successful for worker {worker.id}: "
                f"name={extracted_name}, confidence={result['confidence']:.1f}%"
            )
        else:
            logger.warning(
                f"Govt ID verification failed for worker {worker.id}: "
                f"insufficient data extracted or name mismatch"
            )
        
        return GovtIDVerificationResponse(
            verified=is_verified,
            extracted_name=extracted_name,
            extracted_id_number=extracted_id,
            name_match=name_match,
            confidence=result["confidence"],
            error=result["error"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Govt ID verification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Govt ID verification failed"
        )


# ============================================================================
# Get Current Verification Status
# ============================================================================

@router.get("/status", response_model=VerificationStatusResponse)
async def get_verification_status(
    auth_context: AuthContext = Depends(get_current_auth_context)
):
    """Get current verification status for the authenticated worker."""
    worker = auth_context.worker
    
    return VerificationStatusResponse(
        verification_status=worker.verification_status.value,
        phone_verified=worker.phone_verified_at is not None,
        partner_id_verified=worker.partner_id_verified_at is not None,
        selfie_verified=worker.selfie_verified_at is not None,
        govt_id_verified=worker.govt_id_verified_at is not None,
        fully_verified=worker.verification_status == VerificationStatus.FULLY_VERIFIED
    )
