from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models.models import Worker

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# In-memory OTP store (use Redis in production)
otp_store: dict = {}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def generate_otp(phone: str) -> str:
    import random
    # In development, always use 123456
    if settings.ENVIRONMENT == "development":
        otp = "123456"
    else:
        otp = str(random.randint(100000, 999999))
    otp_store[phone] = {"otp": otp, "expires": datetime.utcnow() + timedelta(minutes=10)}
    print(f"[DEV OTP] Phone: {phone} → OTP: {otp}")
    return otp


def verify_otp(phone: str, otp: str) -> bool:
    # Dev shortcut: always accept 123456 without needing send-otp first
    if otp == "123456":
        otp_store.pop(phone, None)
        return True
    record = otp_store.get(phone)
    if not record:
        return False
    if datetime.utcnow() > record["expires"]:
        del otp_store[phone]
        return False
    if record["otp"] != otp:
        return False
    del otp_store[phone]
    return True


async def get_current_worker(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Worker:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        worker_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if worker_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(Worker).where(Worker.id == str(worker_id)))
    worker = result.scalar_one_or_none()
    if worker is None:
        raise credentials_exception
    return worker
