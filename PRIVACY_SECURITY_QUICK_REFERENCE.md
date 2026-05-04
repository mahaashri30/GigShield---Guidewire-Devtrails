# Privacy & Security Quick Reference 🔐

## The 5 Core Principles

### 1. **ENCRYPT EVERYTHING SENSITIVE** 🔒

| Data Type | Status | How |
|-----------|--------|-----|
| Government ID Photo | ❌ DELETE | Don't store permanently |
| Selfie Photo | ❌ DELETE | S3 auto-delete (30 days) |
| ID Number | ✅ ENCRYPT | AES-256 database encryption |
| Name | ✅ ENCRYPT | AES-256 database encryption |
| Phone Number | ✅ ENCRYPT | AES-256 database encryption |
| In Transit | ✅ ENCRYPT | HTTPS/TLS (256-bit) |
| At Rest | ✅ ENCRYPT | Database encryption + S3 encryption |
| Backups | ✅ ENCRYPT | Encrypted snapshots only |

**How to encrypt:** Use `EncryptedType` from `sqlalchemy-utils` in your models

---

### 2. **NEVER STORE WHAT YOU DON'T NEED** 📵

#### ✅ Store (Minimal Data)
```
- Verification status: "FULLY_VERIFIED" ✓
- Face match score: 0.95 ✓
- Timestamps: When verified ✓
- Phone verified: Yes/No ✓
```

#### ❌ Don't Store (Delete Automatically)
```
- Raw selfie image ✗
- Raw govt ID image ✗
- Face embeddings/templates ✗
- Biometric templates ✗
- Full OCR confidence data ✗
- Raw API responses ✗
```

**Why?** Reduces damage from data breaches. Hacker gets verification status, not your photo or face template.

---

### 3. **CONTROL WHO ACCESSES WHAT** 👥

#### Role Hierarchy
```
ADMIN
├─ Full system access
├─ View worker data
├─ View verification results
├─ View audit logs
└─ Manage users

VERIFICATION_OFFICER
├─ Verify new documents
├─ View verification status
├─ Cannot view raw data
└─ Cannot access audit logs

WORKER
├─ View own data
├─ Download own data
├─ Request data deletion
└─ Cannot view others' data

AUDIT
└─ Read audit logs only
   (WHO accessed WHAT and WHEN)
```

**Implementation:** Check user role before returning data
```python
@router.get("/admin/worker/{id}")
async def get_worker_data(
    user: User = Depends(require_role(UserRole.ADMIN))
):
    # Only ADMIN can see this
```

---

### 4. **LOG EVERYTHING SENSITIVE** 📋

#### What to Log
```
✓ Who accessed data? (user_id, email)
✓ What did they access? (resource_type, resource_id)
✓ When? (timestamp with timezone)
✓ From where? (IP address)
✓ What happened? (success/failed)
✓ Why did it fail? (reason/error)
```

#### What NOT to Log
```
✗ Passwords
✗ API Keys
✗ Raw personal data (only IDs)
✗ Sensitive query parameters
```

#### Example Log Entry
```json
{
  "timestamp": "2024-05-05T14:32:18Z",
  "user_id": "officer_123",
  "user_role": "verification_officer",
  "action": "verify_selfie",
  "resource_type": "worker",
  "resource_id": "worker_456",
  "ip_address": "203.0.113.42",
  "status": "success"
}
```

**Purpose:** Audit trail - detect unauthorized access, prove compliance

---

### 5. **DELETE OLD DATA AUTOMATICALLY** 🗑️

#### Retention Schedule
```
Images (Selfie + Govt ID)
└─ Keep for: 30 days
   └─ Then: Auto-delete from S3 (lifecycle policy)
   └─ Why: Reduces breach risk

Verification Results
└─ Keep for: Indefinite (user's insurance record)
   └─ Then: Never delete (user needs it)

Audit Logs
└─ Keep for: 1 year (compliance requirement)
   └─ Then: Archive to cold storage (Glacier)

Personal Data (Inactive Users)
└─ Keep for: 2 years of inactivity
   └─ Then: Anonymize (can't identify person)
   └─ Example: "name" → "ANONYMIZED_abc123de"
```

**Benefit:** Automatic, no manual work needed. Reduces data at risk.

---

## Quick Implementation Steps

### Step 1: Encrypt Sensitive Fields (Day 1)
```python
# In models.py
from sqlalchemy_utils import EncryptedType

class Worker(Base):
    govt_id_name = Column(EncryptedType(String, ENCRYPTION_KEY))  # ✅
    govt_id_number = Column(EncryptedType(String, ENCRYPTION_KEY))  # ✅
```

### Step 2: Add Audit Logging (Day 1)
```python
# In your endpoints
await AuditService.log_access(
    db=db,
    user_id=user.id,
    action="verify_selfie",
    resource_id=worker_id,
    request=request
)
```

### Step 3: Enforce HTTPS (Day 1)
```python
# In main.py
response.headers["Strict-Transport-Security"] = "max-age=31536000"
```

### Step 4: Add Role Checks (Day 2)
```python
# In your endpoints
async def get_worker_data(
    user: User = Depends(require_role(UserRole.ADMIN))  # ✅
):
```

### Step 5: Set Up Auto-Delete (Day 2)
```bash
# In AWS S3 bucket lifecycle policy
- Expire objects after 30 days
- Delete old versions
```

---

## Compliance Checklist - Simple Version

### ✅ For India (DPDP Act)
```
□ User consents before data collection
□ Privacy policy explains what you collect & why
□ Users can download their data (export)
□ Users can delete their data (right to be forgotten)
□ Data encrypted (in transit & at rest)
□ Access logged (audit trail)
□ Breach plan ready (notify within 72 hours)
```

### ✅ For Users (Trust)
```
□ Clear privacy policy in their language
□ Easy way to contact privacy officer
□ Fast response to data requests
□ No selling data to third parties
□ Regular security updates
```

---

## Real-World Scenarios

### Scenario 1: Data Breach 😰

**What happens:**
```
Hacker gets access to database
    ↓
Finds encrypted govt_id_number ✅ (can't read - encrypted)
Finds encrypted govt_id_name ✅ (can't read - encrypted)
Finds face_match_score: 0.95 ⚠️ (can read - but not sensitive)
Can't find selfie photo ✅ (already deleted after 30 days)
Can't use data to commit fraud ✅ (incomplete information)
```

**Result:** Breach detected, users notified, no major damage

---

### Scenario 2: Rogue Employee 😠

**Attempt:** Employee tries to download all worker photos
```
Employee tries: SELECT * FROM s3://selfies/
    ↓
Audit log shows: access_logs[timestamp].user_id = "emp_123"
    ↓
Admin sees: "Employee viewed 500 selfie photos on unusual time"
    ↓
Alert triggered: "Unusual access pattern detected"
    ↓
Admin investigates: "Why did you access 500 photos?"
    ↓
Employee caught: Audit trail proves unauthorized access
```

**Result:** Employee caught, photos already deleted after 30 days anyway

---

### Scenario 3: User Requests Data Deletion ✅

**User clicks:** "Delete my data"
```
User confirmation page shown
    ↓
System: "Deleting in 30 days (grace period)"
    ↓
Audit log: "Data deletion requested by worker_123"
    ↓
System (automatic): After 30 days → DELETE ALL USER DATA
    ↓
Confirmation email: "Your data has been permanently deleted"
```

**Result:** User's privacy respected, GDPR/DPDP compliant

---

## Common Mistakes to AVOID ❌

```
❌ DON'T: Store images "just in case"
   ✅ DO: Delete after 30 days (S3 lifecycle)

❌ DON'T: Encrypt only some fields
   ✅ DO: Encrypt ALL sensitive data (id, name, phone)

❌ DON'T: Log passwords or API keys
   ✅ DO: Log only user actions and outcomes

❌ DON'T: Allow HTTP connections
   ✅ DO: HTTPS/TLS ONLY

❌ DON'T: Use plaintext passwords
   ✅ DO: Hash with bcrypt (never reversible)

❌ DON'T: Let one role access everything
   ✅ DO: Role-based access control (RBAC)

❌ DON'T: Keep deleted backups forever
   ✅ DO: Auto-delete old backups

❌ DON'T: Log sensitive PII
   ✅ DO: Log only IDs and outcomes

❌ DON'T: Disable security features for "convenience"
   ✅ DO: Security first, convenience second
```

---

## Your System's Privacy Score 📊

| Component | Status | Score |
|-----------|--------|-------|
| Encryption in Transit (HTTPS) | ✅ Ready | 100% |
| Image Auto-Deletion | ✅ Ready | 100% |
| Minimal Data Collection | ✅ Ready | 100% |
| Role-Based Access | 🟡 Needs Implementation | 0% |
| Database Encryption | 🟡 Needs Implementation | 0% |
| Audit Logging | 🟡 Needs Implementation | 0% |
| Data Export Feature | 🟡 Needs Implementation | 0% |
| Data Deletion Feature | 🟡 Needs Implementation | 0% |
| Security Headers | 🟡 Needs Implementation | 0% |
| **TOTAL** | | **50%** |

**Timeline to 100%:** 1-2 weeks (with code provided above)

---

## Resources & Next Steps

### 📚 Compliance Documents
- `GOVT_ID_PRIVACY_SECURITY_GUIDE.md` - Comprehensive guide
- `PRIVACY_SECURITY_IMPLEMENTATION.md` - Code implementation

### 🔐 Implementation Code
See the code files for actual implementation:
1. Database encryption (models.py changes)
2. Audit logging service (audit_service.py)
3. RBAC middleware (auth.py)
4. Security headers (main.py changes)

### 🎯 What to Do Now
1. **This week:** Implement encryption & RBAC
2. **Next week:** Deploy audit logging
3. **After deployment:** Test & monitor audit logs
4. **Ongoing:** Review audit logs weekly for anomalies

### 📞 Questions?
- Privacy concern? Check GOVT_ID_PRIVACY_SECURITY_GUIDE.md
- Implementation question? Check PRIVACY_SECURITY_IMPLEMENTATION.md
- Compliance question? Refer to compliance checklist above

---

**Your system is designed for privacy. Now implement it! 🚀**

