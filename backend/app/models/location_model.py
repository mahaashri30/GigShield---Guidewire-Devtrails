"""
Worker Location Tracking — Secure Implementation
- Coordinates encrypted at rest using Fernet symmetric encryption
- Only last 48 hours of pings retained (auto-purged)
- Used ONLY for GPS spoof detection during claim verification
- Never exposed in API responses
- Worker can request deletion at any time (DPDP Act compliance)
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


def gen_uuid():
    return str(uuid.uuid4())


class WorkerLocationPing(Base):
    __tablename__ = "worker_location_pings"

    id = Column(String, primary_key=True, default=gen_uuid)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False, index=True)

    # Encrypted coordinates — stored as Fernet-encrypted strings, never plain text
    lat_encrypted = Column(Text, nullable=False)
    lng_encrypted = Column(Text, nullable=False)

    # City/pincode derived from coordinates — stored plain for fraud check
    detected_city = Column(String(100), nullable=True)
    detected_pincode = Column(String(10), nullable=True)

    # Speed check — distance from previous ping in km (for spoof detection)
    # >50km in 10min = physically impossible = GPS spoofed
    distance_from_prev_km = Column(Float, nullable=True)
    is_suspicious = Column(Boolean, default=False)

    # Accuracy of GPS reading in meters
    accuracy_meters = Column(Float, nullable=True)

    pinged_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    worker = relationship("Worker", back_populates="location_pings")
