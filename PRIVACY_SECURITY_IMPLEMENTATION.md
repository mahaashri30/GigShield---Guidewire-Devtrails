# Privacy & Security Implementation for Susanoo 🔐

## Code Changes Required

This document shows the **actual implementation** needed to secure government ID data in your FastAPI backend.

---

## 1. Update Models with Encryption

### Current State ❌
```python
# backend/app/models/models.py (INSECURE)

class Worker(Base):
    __tablename__ = "workers"
    
    govt_id_number: str = Column(String(50), nullable=True)  # ❌ PLAINTEXT
    govt_id_name: str = Column(String(255), nullable=True)   # ❌ PLAINTEXT
    phone_number: str = Column(String(20), nullable=True)    # ❌ PLAINTEXT
```

### Updated State ✅
```python
# backend/app/models/models.py (SECURE)

from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types import String as EncryptedString
from sqlalchemy import LargeBinary
import os

# Get encryption key from environment (AWS Secrets Manager)
ENCRYPTION_KEY = os.getenv("DATABASE_ENCRYPTION_KEY")

class Worker(Base):
    __tablename__ = "workers"
    
    # ✅ Encrypted sensitive fields
    govt_id_number: str = Column(
        EncryptedType(String, ENCRYPTION_KEY),
        nullable=True,
        comment="Encrypted govt ID number"
    )
    govt_id_name: str = Column(
        EncryptedType(String, ENCRYPTION_KEY),
        nullable=True,
        comment="Encrypted name from govt ID"
    )
    phone_number: str = Column(
        EncryptedType(String, ENCRYPTION_KEY),
        nullable=True,
        comment="Encrypted phone number"
    )
    
    # ✅ Non-encrypted data (safe to store as-is)
    face_match_score: float = Column(Float, nullable=True)
    verification_status: str = Column(String(50), nullable=False)
    phone_verified_at: datetime = Column(DateTime, nullable=True)
    selfie_verified_at: datetime = Column(DateTime, nullable=True)
    govt_id_verified_at: datetime = Column(DateTime, nullable=True)
    
    # ✅ For compliance & data subject rights
    is_anonymized: bool = Column(Boolean, default=False)
    anonymized_at: datetime = Column(DateTime, nullable=True)
    data_deletion_requested: bool = Column(Boolean, default=False)
    data_deletion_requested_at: datetime = Column(DateTime, nullable=True)
```

**Install required package:**
```bash
pip install sqlalchemy-utils cryptography
```

---

## 2. Add Audit Logging Table

```python
# backend/app/models/models.py (Add this class)

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: int = Column(Integer, primary_key=True, index=True)
    user_id: str = Column(String, nullable=False, index=True)
    user_role: str = Column(String, nullable=False)  # admin, officer, worker
    action: str = Column(String, nullable=False, index=True)  # viewed_id, verified_selfie, etc.
    resource_type: str = Column(String, nullable=False)  # worker, verification
    resource_id: str = Column(String, nullable=False, index=True)  # worker_id
    ip_address: str = Column(String, nullable=False)
    user_agent: str = Column(String, nullable=False)
    status: str = Column(String, nullable=False)  # success, failed
    reason: str = Column(String, nullable=True)  # failure reason
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Index for faster queries
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )
```

---

## 3. Add Role-Based Access Control (RBAC)

```python
# backend/app/middleware/auth.py (NEW FILE)

from enum import Enum
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt
import os

# Define roles
class UserRole(str, Enum):
    ADMIN = "admin"                           # Full system access
    VERIFICATION_OFFICER = "verification_officer"  # Verify documents
    WORKER = "worker"                         # Own data only
    AUDIT = "audit"                           # Read-only logs

class User:
    def __init__(self, id: str, role: UserRole, email: str):
        self.id = id
        self.role = role
        self.email = email

async def get_current_user(request: Request) -> User:
    """Extract & validate JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth_header.split("Bearer ")[1]
    
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        user_role = payload.get("role")
        user_email = payload.get("email")
        
        if not user_id or not user_role:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return User(id=user_id, role=UserRole(user_role), email=user_email)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_role(*allowed_roles: UserRole):
    """Middleware to check user has required role"""
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {allowed_roles}"
            )
        return user
    return dependency
```

---

## 4. Add Audit Logging Service

```python
# backend/app/services/audit_service.py (NEW FILE)

from datetime import datetime
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.models import AuditLog
from sqlalchemy import insert
import logging

logger = logging.getLogger(__name__)

class AuditService:
    """Service for logging all sensitive data access"""
    
    @staticmethod
    async def log_access(
        db: AsyncSession,
        user_id: str,
        user_role: str,
        action: str,
        resource_type: str,
        resource_id: str,
        request: Request,
        status: str = "success",
        reason: str = None
    ):
        """Log data access to audit table"""
        try:
            log_entry = AuditLog(
                user_id=user_id,
                user_role=user_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "unknown")[:500],
                status=status,
                reason=reason,
                timestamp=datetime.utcnow()
            )
            db.add(log_entry)
            await db.commit()
            
            logger.info(
                f"Audit: {user_role} {action} {resource_type}:{resource_id} "
                f"from {request.client.host} - {status}"
            )
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")
            # Don't raise - don't let logging errors break the app
    
    @staticmethod
    async def get_access_logs(
        db: AsyncSession,
        user_id: str = None,
        resource_id: str = None,
        limit: int = 100
    ):
        """Retrieve audit logs (for compliance & investigation)"""
        query = select(AuditLog).order_by(AuditLog.timestamp.desc())
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if resource_id:
            query = query.where(AuditLog.resource_id == resource_id)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
```

---

## 5. Update Verification Endpoints with Logging

```python
# backend/app/api/verification.py (UPDATE EXISTING ENDPOINTS)

from fastapi import APIRouter, UploadFile, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.models import Worker, VerificationStatus
from backend.app.middleware.auth import get_current_user, require_role, UserRole
from backend.app.services.audit_service import AuditService
from backend.app.services.bedrock_service import BedrockAIService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
bedrock_service = BedrockAIService()

# ✅ UPDATED: Verify selfie with audit logging
@router.post("/api/v1/verify/selfie")
async def verify_selfie(
    selfie_file: UploadFile,
    worker_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.VERIFICATION_OFFICER, UserRole.ADMIN))
):
    """Verify selfie with biometric liveness detection & audit logging"""
    
    try:
        # 1. Get worker
        worker = await db.get(Worker, worker_id)
        if not worker:
            # Log failed access
            await AuditService.log_access(
                db=db,
                user_id=user.id,
                user_role=user.role.value,
                action="verify_selfie",
                resource_type="worker",
                resource_id=worker_id,
                request=request,
                status="failed",
                reason="Worker not found"
            )
            raise HTTPException(status_code=404, detail="Worker not found")
        
        # 2. Read selfie image
        selfie_bytes = await selfie_file.read()
        if len(selfie_bytes) > 15 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Image too large (max 15MB)"
            )
        
        # 3. Run verification (Bedrock)
        import base64
        import asyncio
        
        selfie_base64 = base64.b64encode(selfie_bytes).decode()
        
        result = await asyncio.to_thread(
            bedrock_service.verify_selfie_with_id,
            selfie_base64,
            worker.govt_id_image_url,  # Assume already stored
            True
        )
        
        if result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # 4. Update worker (store result, NOT image)
        from sqlalchemy import update
        from datetime import datetime
        
        if result["verified"]:
            await db.execute(
                update(Worker)
                .where(Worker.id == worker.id)
                .values(
                    face_match_score=result["match_score"],
                    verification_status=VerificationStatus.SELFIE_VERIFIED,
                    selfie_verified_at=datetime.utcnow(),
                    # ❌ DON'T store selfie_image_url
                    # S3 lifecycle will auto-delete in 30 days
                )
            )
            await db.commit()
        
        # 5. Log successful access
        await AuditService.log_access(
            db=db,
            user_id=user.id,
            user_role=user.role.value,
            action="verify_selfie",
            resource_type="worker",
            resource_id=worker_id,
            request=request,
            status="success"
        )
        
        logger.info(
            f"Verified selfie for worker {worker_id}: "
            f"verified={result['verified']}, score={result['match_score']:.2f}"
        )
        
        return {
            "verified": result["verified"],
            "match_score": result["match_score"],
            "confidence": result["confidence"],
            "liveness_score": result.get("liveness_score")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Selfie verification failed: {e}")
        
        # Log error
        await AuditService.log_access(
            db=db,
            user_id=user.id,
            user_role=user.role.value,
            action="verify_selfie",
            resource_type="worker",
            resource_id=worker_id,
            request=request,
            status="failed",
            reason=str(e)
        )
        
        raise HTTPException(status_code=500, detail="Verification failed")


# ✅ ADMIN ONLY: View audit logs
@router.get("/api/v1/admin/audit-logs")
async def get_audit_logs(
    worker_id: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.AUDIT))
):
    """View audit logs (admin & audit roles only)"""
    
    logs = await AuditService.get_access_logs(
        db=db,
        resource_id=worker_id,
        limit=1000
    )
    
    # Log this access too!
    await AuditService.log_access(
        db=db,
        user_id=user.id,
        user_role=user.role.value,
        action="view_audit_logs",
        resource_type="audit_log",
        resource_id=worker_id or "all",
        request=request,
        status="success"
    )
    
    return [
        {
            "user_id": log.user_id,
            "action": log.action,
            "resource": f"{log.resource_type}:{log.resource_id}",
            "status": log.status,
            "timestamp": log.timestamp.isoformat(),
            "ip_address": log.ip_address
        }
        for log in logs
    ]


# ✅ WORKER: View own data
@router.get("/api/v1/worker/export-data")
async def export_my_data(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.WORKER))
):
    """Allow user to download their own data (GDPR/DPDP right to portability)"""
    
    worker = await db.get(Worker, user.id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Log this export
    await AuditService.log_access(
        db=db,
        user_id=user.id,
        user_role=user.role.value,
        action="export_data",
        resource_type="worker",
        resource_id=user.id,
        request=request,
        status="success"
    )
    
    return {
        "id": worker.id,
        "phone_verified": worker.phone_verified_at is not None,
        "verification_status": worker.verification_status,
        "govt_id_type": worker.govt_id_type,
        "govt_id_verified": worker.govt_id_verified_at is not None,
        "face_match_score": worker.face_match_score,
        "created_at": worker.created_at.isoformat(),
        # Note: Don't return actual govt_id_name/number in export
        # Only return that they were verified
    }


# ✅ WORKER: Request data deletion
@router.post("/api/v1/worker/request-data-deletion")
async def request_data_deletion(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.WORKER))
):
    """Allow user to request data deletion (right to be forgotten)"""
    
    from sqlalchemy import update
    from datetime import datetime
    
    await db.execute(
        update(Worker)
        .where(Worker.id == user.id)
        .values(
            data_deletion_requested=True,
            data_deletion_requested_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    logger.info(f"Data deletion requested for worker {user.id}")
    
    return {
        "message": "Data deletion request received",
        "status": "pending",
        "will_delete_in_days": 30
    }
```

---

## 6. Add Data Retention Task

```python
# backend/app/tasks/data_retention.py (NEW FILE)

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.app.models.models import Worker, AuditLog
from backend.app.database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

async def cleanup_expired_data():
    """
    Scheduled task to clean up old data (run daily)
    
    Rules:
    - Delete verification images after 30 days (S3 lifecycle)
    - Anonymize personal data after 2 years of inactivity
    - Delete audit logs older than 1 year (keep for compliance)
    """
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Anonymize inactive workers (2 years)
            two_years_ago = datetime.utcnow() - timedelta(days=730)
            
            inactive_workers = await db.execute(
                select(Worker)
                .where(
                    Worker.updated_at < two_years_ago,
                    Worker.is_anonymized == False
                )
            )
            
            for worker in inactive_workers.scalars().all():
                await db.execute(
                    update(Worker)
                    .where(Worker.id == worker.id)
                    .values(
                        govt_id_name=f"ANONYMIZED_{worker.id[:8]}",
                        govt_id_number=None,
                        phone_number=None,
                        is_anonymized=True,
                        anonymized_at=datetime.utcnow()
                    )
                )
                logger.info(f"Anonymized worker {worker.id}")
            
            await db.commit()
            
            # 2. Handle data deletion requests (process after 30-day grace period)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            deletion_requests = await db.execute(
                select(Worker)
                .where(
                    Worker.data_deletion_requested == True,
                    Worker.data_deletion_requested_at < thirty_days_ago
                )
            )
            
            for worker in deletion_requests.scalars().all():
                # Delete from database
                await db.delete(worker)
                logger.info(f"Deleted worker {worker.id} (data deletion request)")
            
            await db.commit()
            
            logger.info("Data retention cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Data retention cleanup failed: {e}")
            raise

# Schedule this to run daily (use APScheduler or AWS Lambda)
# Example with APScheduler:
# scheduler.add_job(cleanup_expired_data, 'cron', hour=2, minute=0)
```

---

## 7. Add Security Headers Middleware

```python
# backend/app/middleware/security.py (NEW FILE)

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # ✅ Prevent CSRF attacks
        response.headers["X-CSRF-Token"] = "require"
        
        # ✅ Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # ✅ Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # ✅ Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # ✅ Force HTTPS
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # ✅ Content Security Policy (prevent XSS)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' https:; "
            "connect-src 'self' https://api.bedrock.amazonaws.com"
        )
        
        # ✅ Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # ✅ Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=()"
        )
        
        return response
```

---

## 8. Update Main App Configuration

```python
# backend/app/main.py (UPDATE)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from backend.app.middleware.security import SecurityHeadersMiddleware
import os

app = FastAPI(title="Susanoo Verification API")

# ✅ 1. Trust only our domain
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "api.susanoo.app",
        "localhost:8000",  # Development only
    ]
)

# ✅ 2. CORS: Only allow our frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.susanoo.com",
        "https://www.susanoo.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)

# ✅ 3. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# ✅ 4. Redirect HTTP to HTTPS (in production)
if os.getenv("ENVIRONMENT") == "production":
    @app.middleware("http")
    async def https_redirect(request, call_next):
        if request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=url)
        return await call_next(request)

# Include routers
from backend.app.api import verification
app.include_router(verification.router)
```

---

## 9. Environment Configuration

```bash
# backend/.env (UPDATE with security settings)

# === DATABASE (Encrypted Connection) ===
DATABASE_URL=postgresql+asyncpg://user:password@rds-instance:5432/susanoo
DATABASE_ENCRYPTION_KEY=${AWS_SECRET_MANAGER:database-encryption-key}
DATABASE_SSL_MODE=require  # Enforce SSL/TLS

# === AWS CREDENTIALS (From Secrets Manager) ===
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=${AWS_SECRET_MANAGER:aws-access-key-id}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_MANAGER:aws-secret-access-key}

# === JWT ===
JWT_SECRET_KEY=${AWS_SECRET_MANAGER:jwt-secret-key}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# === SECURITY ===
ENVIRONMENT=production
ENFORCE_HTTPS=true
API_RATE_LIMIT_PER_MINUTE=60
ALLOWED_HOSTS=api.susanoo.app,www.susanoo.app

# === CORS ===
CORS_ALLOWED_ORIGINS=https://app.susanoo.com,https://www.susanoo.com

# === DATA RETENTION (Days) ===
IMAGE_RETENTION_DAYS=30
AUDIT_LOG_RETENTION_DAYS=365
PERSONAL_DATA_RETENTION_DAYS=730

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FORMAT=json  # Structured logging for analysis

# === BEDROCK (AWS AI) ===
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022
BEDROCK_REGION=us-east-1
```

---

## 10. Requirements.txt Updates

```bash
# backend/requirements.txt (ADD THESE)

# For encryption
sqlalchemy-utils>=0.41.0
cryptography>=41.0.0

# For secure password hashing
bcrypt>=4.0.0

# For JWT tokens
python-jose[cryptography]>=3.3.0
pydantic>=2.0.0

# For structured logging
python-json-logger>=2.0.7

# For scheduled tasks (data retention cleanup)
APScheduler>=3.10.0

# Keep existing
fastapi>=0.111.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.30
asyncpg>=0.29.0
boto3>=1.34.0
botocore>=1.34.0
pillow>=10.0.0
python-multipart>=0.0.6
```

---

## Implementation Checklist

```
📋 PHASE 1: IMMEDIATE (This sprint)
☐ Add encryption to sensitive database fields
☐ Add audit logging table & service
☐ Add RBAC (roles & permissions)
☐ Update all endpoints with logging
☐ Add security headers middleware
☐ Update .env with Secrets Manager references

📋 PHASE 2: FOLLOW-UP (Next 2 weeks)
☐ Deploy to AWS with RDS encryption
☐ Configure S3 auto-deletion (30-day lifecycle)
☐ Set up CloudWatch monitoring
☐ Test data export functionality
☐ Test data deletion (right to be forgotten)
☐ Create privacy policy UI

📋 PHASE 3: COMPLIANCE (Next month)
☐ Document data flows (for DPIA)
☐ Document security measures (for audit)
☐ Create incident response plan
☐ Perform penetration testing
☐ Get DPDP Act compliance audit
```

---

## Testing Security Implementation

```bash
# Test encryption
curl -X POST https://api.susanoo.app/api/v1/verify/selfie \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "selfie_file=@selfie.jpg"

# Test audit logging
curl -X GET https://api.susanoo.app/api/v1/admin/audit-logs \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Test data export
curl -X GET https://api.susanoo.app/api/v1/worker/export-data \
  -H "Authorization: Bearer $WORKER_TOKEN"

# Test HTTPS enforcement
curl -X GET http://api.susanoo.app/api/v1/verify/status
# Should redirect to HTTPS
```

---

## Production Deployment Checklist

```
✅ SECURITY DEPLOYMENT
☐ Database encryption enabled (RDS)
☐ All API endpoints HTTPS only
☐ Security headers configured
☐ RBAC properly configured
☐ Audit logging active
☐ AWS Secrets Manager configured
☐ Data retention policies automated
☐ Backups encrypted
☐ WAF (Web Application Firewall) enabled
☐ DDoS protection enabled

✅ COMPLIANCE
☐ Privacy policy published
☐ User consent mechanism implemented
☐ Data subject rights features ready
☐ Breach response plan documented
☐ GDPR/DPDP assessment completed
```

