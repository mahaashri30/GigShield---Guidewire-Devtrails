"""
Fraud Detection Engine - Phase 1 (Rule-Based)
Phase 2 will add Isolation Forest ML model
"""
import json
from datetime import datetime, timedelta, timezone
from typing import List


def _utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def calculate_fraud_score(
    worker_city: str,
    event_city: str,
    worker_pincode: str,
    event_pincode: str,
    was_platform_active: bool,
    claims_this_week: int,
    claims_same_event: int,
    event_started_at: datetime,
    claim_created_at: datetime,
    last_known_city: str = "",
    had_suspicious_ping: bool = False,
) -> dict:
    """
    Rule-based fraud scoring (0 = clean, 100 = definite fraud).
    Returns score and list of flags triggered.
    """
    score = 0.0
    flags = []

    # Rule 1: City mismatch
    if worker_city.lower() != event_city.lower():
        score += 40
        flags.append(f"CITY_MISMATCH: Worker in {worker_city}, event in {event_city}")

    # Rule 1b: Last GPS location mismatch (anti-spoofing)
    if last_known_city and last_known_city.lower() != event_city.lower():
        score += 35
        flags.append(f"GPS_LOCATION_MISMATCH: Last GPS ping shows {last_known_city}, event in {event_city}")

    # Rule 2: Worker not active on platform during event
    if not was_platform_active:
        score += 25
        flags.append("PLATFORM_INACTIVE: Worker not logged in during disruption window")

    # Rule 3: Too many claims this week
    if claims_this_week >= 5:
        score += 20
        flags.append(f"HIGH_CLAIM_FREQUENCY: {claims_this_week} claims this week")
    elif claims_this_week >= 3:
        score += 10
        flags.append(f"ELEVATED_CLAIM_FREQUENCY: {claims_this_week} claims this week")

    # Rule 4: Duplicate claim for same event
    if claims_same_event >= 1:
        score += 50
        flags.append("DUPLICATE_CLAIM: Already claimed this disruption event")

    # Rule 5: Claim filed suspiciously fast (< 30 seconds after event)
    # Normalise to UTC-aware before subtracting to avoid TypeError with mixed
    # naive/aware datetimes (event_started_at from DB is aware, claim_created_at
    # from datetime.utcnow() was naive)
    time_delta = (_utc(claim_created_at) - _utc(event_started_at)).total_seconds()
    if 0 < time_delta < 30:
        score += 15
        flags.append(f"SUSPICIOUS_SPEED: Claim filed {time_delta:.0f}s after event start")

    # Rule 6: Suspicious GPS ping detected (impossible movement speed)
    if had_suspicious_ping:
        score += 30
        flags.append("GPS_SPOOF_DETECTED: Impossible movement speed in location history")

    score = min(score, 100.0)

    return {
        "fraud_score": round(score, 2),
        "flags": flags,
        "flags_json": json.dumps(flags),
        "auto_approve": score < 30,
        "hold_for_review": 30 <= score < 70,
        "auto_reject": score >= 70,
        "verdict": (
            "APPROVED" if score < 30
            else "REVIEW" if score < 70
            else "REJECTED"
        ),
    }
