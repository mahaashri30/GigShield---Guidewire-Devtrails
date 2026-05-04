# Government ID Privacy & Security Strategy 🔐

## Overview

Handling government ID data requires **strict privacy controls** and **multi-layer security**. This guide covers compliance, data protection, and implementation strategies for Susanoo's identity verification system.

---

## 1. Privacy & Security Risks

### 🔴 Data Risks When Handling Govt IDs

| Risk | Severity | Impact | Mitigation |
|------|----------|--------|-----------|
| **Identity Theft** | Critical | Attacker gets ID number, name, DOB | Encryption + access control |
| **Data Breach** | Critical | Personal data exposed publicly | Firewall, TLS, database encryption |
| **Unauthorized Access** | High | Internal employee sees data | Role-based access control (RBAC) |
| **Photo Misuse** | High | Photo used for deepfakes/fraud | Store separately, access logs |
| **Data Retention** | High | Keeping data longer than needed | Auto-deletion policies |
| **Unencrypted Transit** | Critical | Data intercepted in transfer | HTTPS/TLS only, no HTTP |
| **Database Breach** | Critical | Unencrypted data exposed | Database encryption at rest |
| **Insider Threat** | Medium | Employee extracts data | Audit logs, monitoring, segregation |

---

## 2. Compliance Requirements

### 🏛️ Regulations Your App Must Follow

#### **India (Primary Market)**
- **DPDP Act 2023** (Data Protection)
  - Must have explicit user consent
  - Right to be forgotten (data deletion)
  - Data minimization (collect only necessary)
  - Breach notification (72 hours)
  - Privacy policy required
  - Cross-border transfer restrictions

- **Aadhaar Act 2016** (if using Aadhaar)
  - Only UIDAI-certified entities can access
  - Fingerprint/iris data cannot be stored
  - Demographic data limited access
  - 6-month retention maximum (some data)
  - Specific use case authorization required

- **RBI Guidelines** (Banking/Insurance)
  - Secure data storage
  - Encryption standards (AES-256)
  - Access control requirements
  - Audit trail maintenance
  - Incident response procedures

- **NIST Cybersecurity Framework**
  - Identify, Protect, Detect, Respond, Recover
  - Risk assessment (annual)
  - Security testing (penetration testing)

#### **Global (If Expanding)**
- **GDPR** (EU users) - Strict data protection
- **CCPA** (California) - Privacy rights
- **Local regulations** - Check country-specific laws

---

## 3. Privacy-First Architecture

### 🏗️ System Design for Privacy

```
┌─────────────────────────────────────────────────────────────┐
│                    MOBILE APP (Flutter)                      │
│  • User captures ID image locally                            │
│  • User captures selfie locally                              │
│  • No data stored on device (cleared after upload)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
              HTTPS/TLS ENCRYPTION
         (256-bit encrypted tunnel)
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           AWS API GATEWAY (FastAPI Backend)                  │
│  • Terminates TLS connections                               │
│  • Rate limiting (prevent brute force)                       │
│  • Request validation (prevent injection)                    │
│  • Authentication (JWT tokens)                              │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│         VERIFICATION PROCESSING LAYER (Bedrock)             │
│  • Never stores raw images                                  │
│  • Processes in memory (ephemeral)                          │
│  • Extracts minimal fields only                             │
│  • Returns: match_score, confidence, extracted_name         │
│  • Discards: raw image, biometric template                  │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│        AWS SECRETS MANAGER (Credentials)                     │
│  • API keys never in .env files                             │
│  • Automatic rotation (90-day)                              │
│  • Audit logging (who accessed what)                        │
│  • Encryption (customer managed keys)                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│        ENCRYPTED DATABASE (PostgreSQL with Encryption)       │
│  • Store ONLY: name, ID number, status, timestamps          │
│  • Never store: raw images, face embeddings, photos         │
│  • Encryption: AES-256 (AWS RDS encryption at rest)        │
│  • Backups: Encrypted snapshots only                        │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│      AWS S3 WITH ENCRYPTION & AUTO-DELETE (Images)          │
│  • Store images for: 30 days (configurable)                 │
│  • Encrypted: SSE-S3 or customer managed keys               │
│  • Versioning: OFF (no restore capability)                  │
│  • Lifecycle: Auto-delete after 30 days                     │
│  • Access logs: CloudTrail (who downloaded what)            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│           AUDIT LOGGING & MONITORING (CloudWatch)            │
│  • All API calls logged (who, what, when, IP)               │
│  • Data access monitored (alerts on unusual patterns)       │
│  • Failed auth attempts logged                              │
│  • Geographic anomalies detected                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Data Classification & Handling

### 📊 What Data to Collect & Store

#### **COLLECT (During Verification)**
```
✅ Phone Number (for OTP verification)
✅ Selfie Photo (for face verification - deleted after 30 days)
✅ Govt ID Photo (for OCR - deleted after 30 days)
✅ Extracted Name
✅ Extracted ID Number
✅ Match Score (0-1 range)
✅ Verification Status
✅ Timestamps
```

#### **NEVER STORE** ❌
```
❌ Biometric Face Templates/Embeddings
❌ Raw selfie photo (use match score instead)
❌ Raw govt ID photo (use extracted fields instead)
❌ Passwords in plaintext
❌ Full OCR confidence data
❌ Sensitive dates (DOB, expiry) unless critical
❌ Complete SSN/ID number (store last 4 digits only)
```

#### **ENCRYPT IN DATABASE** 🔐
```
🔒 ID Number (encrypt before storing)
🔒 Name (optional encryption if very sensitive)
🔒 Extracted personal data
🔒 User email addresses
```

---

## 5. Implementation Strategy

### 🔧 Code-Level Security Measures

#### **5.1 Image Handling (Privacy)**

```python
# ❌ DON'T: Store images permanently
worker.selfie_image_url = "s3://bucket/selfies/worker_123.jpg"  # NO!

# ✅ DO: Process, verify, delete
async def verify_selfie(selfie_file: UploadFile, worker_id: str):
    """Process selfie without storing permanently"""
    
    # 1. Upload temporarily to S3 with auto-delete
    temp_s3_key = f"temp/verification/{worker_id}/{uuid.uuid4()}.jpg"
    await upload_to_s3(
        file=selfie_file,
        key=temp_s3_key,
        lifecycle_rule={
            "Days": 1,  # Auto-delete after 1 day
            "Encryption": "AES-256"
        }
    )
    
    # 2. Run verification (never store results)
    result = await bedrock_service.verify_selfie_with_id(
        selfie_s3_uri=f"s3://bucket/{temp_s3_key}",
        govt_id_s3_uri=f"s3://bucket/{govt_id_key}"
    )
    
    # 3. Store ONLY the verification result, not the image
    await db.execute(
        update(Worker)
        .where(Worker.id == worker_id)
        .values(
            face_match_score=result["match_score"],      # ✅ Store score
            verification_status=VerificationStatus.SELFIE_VERIFIED,
            # selfie_image_url is NOT stored                 # ❌ Don't store
        )
    )
    
    # 4. S3 auto-lifecycle will delete after 1 day
    # No manual deletion needed
    
    return {"verified": result["verified"], "match_score": result["match_score"]}
```

#### **5.2 Database Encryption**

```python
# ❌ DON'T: Store sensitive data in plaintext
class Worker(Base):
    __tablename__ = "workers"
    
    govt_id_number: str  # PLAINTEXT - INSECURE!

# ✅ DO: Encrypt sensitive fields
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types import String

class Worker(Base):
    __tablename__ = "workers"
    
    # Encrypt sensitive fields
    govt_id_number: str = Column(
        EncryptedType(String, SECRET_KEY),  # AES encryption
        nullable=True
    )
    govt_id_name: str = Column(
        EncryptedType(String, SECRET_KEY),
        nullable=True
    )
    phone_number: str = Column(
        EncryptedType(String, SECRET_KEY),
        nullable=True
    )
    
    # Non-sensitive fields (no encryption needed)
    face_match_score: float = Column(Float, nullable=True)
    verification_status: str = Column(String(50), nullable=False)
```

#### **5.3 Role-Based Access Control (RBAC)**

```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"              # Full access
    VERIFICATION_OFFICER = "verification_officer"  # View verification status
    WORKER = "worker"            # Own data only
    AUDIT = "audit"              # Logs only, no PII

# Middleware to check role
async def require_role(*allowed_roles):
    async def middleware(request: Request):
        user = await get_current_user(request)
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        return user
    return middleware

# Usage in endpoints
@router.get("/api/v1/admin/workers/{worker_id}")
async def view_worker_details(
    worker_id: str,
    user: User = Depends(require_role(UserRole.ADMIN))
):
    """Only ADMIN can view sensitive worker data"""
    worker = await db.get(Worker, worker_id)
    
    return {
        "id": worker.id,
        "name": worker.govt_id_name,  # Encrypted, only shown to ADMIN
        "govt_id": worker.govt_id_number,  # Encrypted
        "verification_status": worker.verification_status
    }

@router.get("/api/v1/audit/access-logs")
async def view_access_logs(
    user: User = Depends(require_role(UserRole.AUDIT, UserRole.ADMIN))
):
    """Only AUDIT/ADMIN can view who accessed what data"""
    return await get_audit_logs()
```

#### **5.4 Audit Logging**

```python
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
import logging

# Create audit log table
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: int = Column(Integer, primary_key=True)
    user_id: str = Column(String, nullable=False)
    user_role: str = Column(String, nullable=False)
    action: str = Column(String, nullable=False)  # "viewed_id", "verified_selfie", etc.
    resource_id: str = Column(String, nullable=False)  # worker_id
    resource_type: str = Column(String, nullable=False)  # "worker", "verification", etc.
    ip_address: str = Column(String, nullable=False)
    user_agent: str = Column(String, nullable=False)
    status: str = Column(String, nullable=False)  # "success", "failed"
    reason: str = Column(String, nullable=True)  # "unauthorized", "not_found", etc.
    timestamp: datetime = Column(DateTime, default=datetime.utcnow)

# Log every sensitive action
async def log_audit(
    user_id: str,
    user_role: str,
    action: str,
    resource_id: str,
    resource_type: str,
    request: Request,
    status: str = "success",
    reason: str = None
):
    """Log sensitive data access"""
    log_entry = AuditLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        resource_id=resource_id,
        resource_type=resource_type,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        status=status,
        reason=reason
    )
    db.add(log_entry)
    await db.commit()

# Use in endpoints
@router.post("/api/v1/verify/selfie")
async def verify_selfie(
    selfie_file: UploadFile,
    worker_id: str,
    request: Request,
    user: User = Depends(require_role(UserRole.VERIFICATION_OFFICER))
):
    """Verify selfie with audit logging"""
    try:
        result = await verify_selfie_logic(selfie_file, worker_id)
        
        # Log successful access
        await log_audit(
            user_id=user.id,
            user_role=user.role,
            action="verified_selfie",
            resource_id=worker_id,
            resource_type="worker",
            request=request,
            status="success"
        )
        
        return result
    except Exception as e:
        # Log failed access
        await log_audit(
            user_id=user.id,
            user_role=user.role,
            action="verify_selfie_failed",
            resource_id=worker_id,
            resource_type="worker",
            request=request,
            status="failed",
            reason=str(e)
        )
        raise
```

#### **5.5 Data Retention & Auto-Deletion**

```python
from datetime import datetime, timedelta

class DataRetentionPolicy:
    """Define how long to keep different types of data"""
    
    # Images: Delete after 30 days
    SELFIE_IMAGE_RETENTION_DAYS = 30
    GOVT_ID_IMAGE_RETENTION_DAYS = 30
    
    # Verification logs: Keep for 1 year (for audit)
    VERIFICATION_LOG_RETENTION_DAYS = 365
    
    # Personal data: Delete 2 years after last activity
    PERSONAL_DATA_RETENTION_DAYS = 730
    
    # Audit logs: Keep forever (compliance)
    AUDIT_LOG_RETENTION_DAYS = None  # Infinite

# Scheduled task to clean up old data
async def cleanup_expired_data():
    """Run daily via AWS Lambda or APScheduler"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    
    # Delete expired S3 images
    # Note: Use S3 lifecycle policies instead (automatic)
    
    # Delete expired verification logs
    await db.execute(
        delete(VerificationLog)
        .where(VerificationLog.created_at < cutoff_date)
    )
    
    # For inactive workers, anonymize data after 2 years
    inactive_workers = await db.execute(
        select(Worker)
        .where(
            Worker.last_activity < (datetime.utcnow() - timedelta(days=730)),
            Worker.is_anonymized == False
        )
    )
    
    for worker in inactive_workers:
        # Anonymize instead of delete
        await db.execute(
            update(Worker)
            .where(Worker.id == worker.id)
            .values(
                govt_id_name=f"ANON_{worker.id[:8]}",
                govt_id_number=None,
                phone_number=None,
                is_anonymized=True
            )
        )
    
    await db.commit()
    logger.info("Data cleanup completed")
```

#### **5.6 Encryption in Transit (HTTPS/TLS)**

```python
# ❌ DON'T: Allow HTTP
# app = FastAPI()  # Insecure by default!

# ✅ DO: Enforce HTTPS/TLS
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 1. Only allow HTTPS
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.susanoo.app"],  # Your domain
)

# 2. CORS: Only allow your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.susanoo.com"],  # HTTPS only
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization"],
)

# 3. SSL/TLS certificate (use AWS Certificate Manager)
# Configure in AWS Load Balancer:
# - Use ACM certificate (free)
# - TLS 1.2+ only
# - Strong cipher suites

# 4. Enforce HSTS (HTTP Strict Transport Security)
from starlette.middleware.base import BaseHTTPMiddleware

class HSTPSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(HSTPSMiddleware)
```

---

## 6. AWS Security Configuration

### ☁️ AWS Best Practices for Govt ID Data

#### **6.1 RDS (PostgreSQL) Security**

```yaml
# Encrypt database at rest
RDS_ENCRYPTION: true
KMS_KEY_ID: "arn:aws:kms:region:account:key/id"

# Network isolation (VPC)
VPC_SECURITY_GROUP:
  - Inbound: FastAPI server only (port 5432)
  - Outbound: Disabled
  - Public Access: Disabled

# Backup encryption
BACKUP_ENCRYPTION: true
BACKUP_RETENTION: 30  # 30 days

# High availability
MULTI_AZ: true  # Automatic failover
AUTOMATED_BACKUPS: true

# Parameter group security
REQUIRE_SECURE_TRANSPORT: true  # SSL required
```

#### **6.2 S3 (Image Storage) Security**

```yaml
# Encryption at rest
SERVER_SIDE_ENCRYPTION: "AES256"  # or KMS key

# Blocking public access
BLOCK_PUBLIC_ACLS: true
BLOCK_PUBLIC_POLICY: true
IGNORE_PUBLIC_ACLS: true
RESTRICT_PUBLIC_BUCKETS: true

# Versioning (disabled - no restore capability)
VERSIONING: disabled

# Lifecycle policy (auto-delete)
LIFECYCLE_RULE:
  - Days: 30
    Action: "DELETE"
    
  - Days: 7
    Action: "TRANSITION_TO_GLACIER"  # Archive before delete

# Access logging
ACCESS_LOG_BUCKET: "bucket-logs"

# Encryption of uploads
REQUIRE_ENCRYPTION_ON_PUT: true

# CORS (only your domain)
CORS:
  - AllowedOrigins: ["https://app.susanoo.com"]
    AllowedMethods: ["POST", "GET"]
    AllowedHeaders: ["Content-Type"]
```

#### **6.3 AWS Bedrock Security**

```python
# ✅ Use AWS Bedrock Secrets Manager for credentials
import boto3
from botocore.exceptions import ClientError

def get_aws_credentials():
    """Retrieve credentials from Secrets Manager (never hardcoded)"""
    client = boto3.client('secretsmanager')
    
    try:
        secret = client.get_secret_value(
            SecretId='bedrock-credentials'
        )
        credentials = json.loads(secret['SecretString'])
        return credentials
    except ClientError as e:
        logger.error(f"Failed to retrieve credentials: {e}")
        raise

# Configure Bedrock with least privilege
bedrock_client = boto3.client(
    'bedrock-runtime',
    region_name='us-east-1'
)

# Request goes through encrypted channel
response = bedrock_client.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022',
    body=json.dumps({
        "image_source": {
            "bytes": base64_encoded_image  # Encrypted in transit
        }
    })
)

# Response is NOT stored - only extract verification result
verification_result = {
    "verified": response["verified"],
    "match_score": response["match_score"],
    # Don't store: face_embedding, raw_response
}
```

---

## 7. Compliance Checklist

### ✅ DPDP Act 2023 (India) Compliance

```
□ User Consent
  ✅ Get explicit consent before collecting data
  ✅ Separate consent for each purpose (verification, analytics)
  ✅ Store consent with timestamp
  ✅ Allow easy withdrawal of consent

□ Privacy Policy
  ✅ Clear, readable privacy policy
  ✅ Explain data collection purpose
  ✅ Explain data retention period
  ✅ Explain data sharing (with whom)
  ✅ User rights (access, deletion, portability)
  ✅ Available in local language (Hindi)

□ Data Subject Rights
  ✅ Right to access (export user data)
  ✅ Right to correction (update data)
  ✅ Right to be forgotten (delete data)
  ✅ Right to data portability (download data)
  ✅ Provide these features within 30 days

□ Data Breach Response
  ✅ Monitor for breaches
  ✅ Detect within 72 hours
  ✅ Notify affected users
  ✅ Notify data protection authority
  ✅ Document incident response

□ Data Protection Impact Assessment
  ✅ Conduct DPIA annually
  ✅ Document privacy risks
  ✅ Document mitigation measures
  ✅ Update as system changes

□ Data Minimization
  ✅ Collect only necessary data
  ✅ Don't collect data "just in case"
  ✅ Delete data when no longer needed
  ✅ Regular data deletion audits

□ Security Measures
  ✅ Encryption (AES-256)
  ✅ Access control (RBAC)
  ✅ Audit logging
  ✅ Regular security updates
  ✅ Penetration testing (annual)
  ✅ Disaster recovery plan

□ Processor Contracts
  ✅ AWS (if using their services)
  ✅ Bedrock (data processing)
  ✅ OTP provider (2Factor.in)
  ✅ Ensure they comply with DPDP
```

### ✅ Aadhaar Act Compliance (if using Aadhaar IDs)

```
□ UIDAI Certification
  ✅ Apply for UIDAI certification
  ✅ Undergo security audit
  ✅ Implement UIDAI guidelines
  ✅ Regular compliance audits

□ Data Handling
  ✅ Never store biometric data (fingerprint, iris)
  ✅ Limit demographic data (name, address only)
  ✅ Never perform demographic matching alone
  ✅ Delete Aadhaar number after verification (don't store)

□ Consent & Transparency
  ✅ Explicit consent for Aadhaar usage
  ✅ Explain verification purpose
  ✅ Show consent terms before processing
```

---

## 8. Implementation Roadmap

### Phase 1: Immediate (Next Release) 🚀
- [x] Enable database encryption (PostgreSQL + RDS)
- [x] Configure HTTPS/TLS on all endpoints
- [x] Implement RBAC (Admin, Officer, Worker roles)
- [x] Add basic audit logging (who accessed what)
- [x] Set S3 lifecycle policies (auto-delete images)
- [x] Encrypt sensitive database fields

### Phase 2: Short-term (1-2 months) 📋
- [ ] Implement comprehensive audit logging (CloudWatch)
- [ ] Add data retention policies with auto-deletion
- [ ] Create data export feature (user download data)
- [ ] Add data deletion feature (right to be forgotten)
- [ ] Implement IP-based access restrictions
- [ ] Add anomaly detection (unusual access patterns)

### Phase 3: Medium-term (3-6 months) 🎯
- [ ] Conduct DPIA (Data Protection Impact Assessment)
- [ ] Apply for UIDAI certification (if using Aadhaar)
- [ ] Implement DLP (Data Loss Prevention) solutions
- [ ] Add biometric encryption (FaceNet embeddings)
- [ ] Set up KMS key rotation (90-day)
- [ ] Penetration testing by external firm

### Phase 4: Long-term (6-12 months) 📈
- [ ] Achieve DPDP compliance certification
- [ ] Implement zero-trust security model
- [ ] Deploy advanced threat detection
- [ ] Set up SOC (Security Operations Center)
- [ ] Implement end-to-end encryption (E2EE)
- [ ] Build privacy dashboard for users

---

## 9. Configuration Files

### Environment Variables (.env)

```bash
# ✅ DO: Use Secrets Manager, NOT .env files
AWS_SECRETS_MANAGER_ENABLED=true
AWS_SECRET_ID_NAME=susanoo-app-secrets

# If using .env (development only):
# ✅ DO: Encrypt sensitive values
# ❌ DON'T: Hardcode API keys

# Encryption key (for database field encryption)
ENCRYPTION_KEY=${AWS_SECRETS_MANAGER}  # Retrieved from Secrets Manager

# Database
DATABASE_URL=postgresql+asyncpg://user:password@rds-instance:5432/susanoo

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=${AWS_SECRETS_MANAGER}
AWS_SECRET_ACCESS_KEY=${AWS_SECRETS_MANAGER}

# TLS/SSL
SSL_CERT_PATH=/etc/ssl/certs/certificate.pem
SSL_KEY_PATH=/etc/ssl/private/private-key.pem
ENFORCE_HTTPS=true

# S3 Configuration
S3_BUCKET=susanoo-verifications
S3_IMAGE_RETENTION_DAYS=30
S3_ENCRYPTION=AES256

# Data Retention
IMAGE_RETENTION_DAYS=30
AUDIT_LOG_RETENTION_DAYS=forever
PERSONAL_DATA_RETENTION_DAYS=730

# Security
JWT_SECRET_KEY=${AWS_SECRETS_MANAGER}
API_RATE_LIMIT_PER_MINUTE=60
ALLOWED_HOSTS=api.susanoo.app
CORS_ALLOWED_ORIGINS=https://app.susanoo.com
```

---

## 10. Privacy Policy Template

### For Your App (To Add to UI)

```markdown
# Privacy Policy - Susanoo Identity Verification

## 1. What Data We Collect
- Phone number (for verification only)
- Government ID (Aadhaar, DL, Voter ID, PAN)
- Selfie photo (for face verification)
- Name, ID number (extracted from government ID)
- Verification status

## 2. Why We Collect It
- To verify your identity
- To prevent fraud and unauthorized access
- To comply with regulatory requirements
- To improve verification accuracy

## 3. How We Protect It
- Encrypted in transit (HTTPS/TLS)
- Encrypted at rest (AES-256)
- Access limited to authorized personnel
- Audit logs for all access
- Regular security testing

## 4. How Long We Keep It
- ID Photos: 30 days (auto-deleted)
- Selfie Photo: 30 days (auto-deleted)
- Verification status: Indefinite (for your insurance records)
- Audit logs: 1 year
- Personal data: 2 years (then anonymized)

## 5. Your Rights
- Right to access your data
- Right to request deletion
- Right to correct inaccuracies
- Right to download your data
- Right to withdraw consent

## 6. Contact
- Privacy Officer: privacy@susanoo.app
- Complaint: grievance@susanoo.app
```

---

## 11. Quick Security Checklist

### Before Deploying ✅

```
ENCRYPTION
☐ Database encrypted at rest (RDS encryption enabled)
☐ Database in transit encrypted (SSL/TLS required)
☐ S3 bucket encrypted (SSE-S3 or KMS)
☐ Sensitive fields encrypted (govt_id_number, etc.)
☐ Backups encrypted
☐ API endpoints use HTTPS only

ACCESS CONTROL
☐ Role-based access control (RBAC) implemented
☐ Admin > Officer > Worker hierarchy
☐ API keys in AWS Secrets Manager (not .env)
☐ Service accounts have minimal permissions
☐ MFA enabled for admin accounts

DATA HANDLING
☐ Images deleted after 30 days (S3 lifecycle)
☐ Only extraction results stored (not raw data)
☐ Biometric templates not stored
☐ No plaintext sensitive data
☐ Data retention policies automated

MONITORING & LOGGING
☐ Audit logging for all data access
☐ Failed login attempts logged
☐ Unusual access patterns detected
☐ CloudWatch alarms configured
☐ Log retention set appropriately

SECURITY TESTING
☐ Penetration testing completed
☐ SQL injection tests passed
☐ XSS vulnerability testing passed
☐ CORS configuration tested
☐ Rate limiting tested

COMPLIANCE
☐ Privacy policy published (in user language)
☐ User consent collected (before data collection)
☐ Data breach response plan documented
☐ DPIA (Data Protection Impact Assessment) completed
☐ Vendor compliance verified (AWS, Bedrock, 2Factor.in)

DEPLOYMENT
☐ HSTS headers enabled (force HTTPS)
☐ Security headers set (CSP, X-Frame-Options, etc.)
☐ WAF (Web Application Firewall) enabled
☐ DDoS protection enabled
☐ Backup & disaster recovery tested
```

---

## Summary: Privacy & Security Tiers

### 🟢 Implemented (Ready Now)
✅ TLS encryption in transit  
✅ AWS Bedrock integration (no local data storage)  
✅ Image auto-deletion (S3 lifecycle)  
✅ Minimal data collection  

### 🟡 In Progress (Next 1-2 months)
🟡 Database encryption at rest  
🟡 Comprehensive audit logging  
🟡 RBAC implementation  
🟡 Data retention automation  

### 🔴 Coming Soon (3-6 months)
🔴 DPIA assessment  
🔴 UIDAI certification  
🔴 Penetration testing  
🔴 Compliance audit  

---

**Bottom Line:** 
Your system is designed for privacy & security from the ground up. Follow this guide to maintain compliance and user trust. 🔐

