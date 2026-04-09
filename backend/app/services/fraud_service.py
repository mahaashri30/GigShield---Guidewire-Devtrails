"""
Fraud Detection Engine - Phase 1 (Rule-Based)
Phase 2 will add Isolation Forest ML model
"""
import json
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import List
from app.models.models import DisruptionType

# Load Isolation Forest model and scaler if available
# Trained via ml/fraud_detection/train.py
_MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../ml/fraud_detection/")
_model_path = os.path.join(_MODEL_DIR, "model.joblib")
_scaler_path = os.path.join(_MODEL_DIR, "scaler.joblib")

try:
    _fraud_model = joblib.load(_model_path)
    _scaler = joblib.load(_scaler_path)
except Exception:
    _fraud_model = None
    _scaler = None

_TYPE_MAP = {
    DisruptionType.HEAVY_RAIN: 0,
    DisruptionType.EXTREME_HEAT: 1,
    DisruptionType.AQI_SPIKE: 2,
    DisruptionType.TRAFFIC_DISRUPTION: 3,
    DisruptionType.CIVIC_EMERGENCY: 4,
}


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
    disruption_type: DisruptionType = DisruptionType.HEAVY_RAIN,
    last_known_city: str = "",
    had_suspicious_ping: bool = False,
    claim_amount_ratio: float = 1.0,
    active_hours_ratio: float = 1.0,
) -> dict:
    """
    Hybrid fraud scoring: rule-based + Isolation Forest ML.
    Returns score and list of flags triggered.
    """
    score = 0.0
    flags = []

    # Rule 1: City mismatch
    city_match = 1 if worker_city.lower() == event_city.lower() else 0
    if city_match == 0:
        score += 40
        flags.append(f"CITY_MISMATCH: Worker in {worker_city}, event in {event_city}")

    # Rule 1b: Last GPS location mismatch (anti-spoofing)
    gps_city_match = 1
    if last_known_city and last_known_city.lower() != event_city.lower():
        gps_city_match = 0
        score += 35
        flags.append(f"GPS_LOCATION_MISMATCH: Last GPS ping shows {last_known_city}, event in {event_city}")

    # Rule 2: Worker not active on platform during event
    platform_active = 1 if was_platform_active else 0
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
    time_delta = (_utc(claim_created_at) - _utc(event_started_at)).total_seconds()
    if 0 < time_delta < 30:
        score += 15
        flags.append(f"SUSPICIOUS_SPEED: Claim filed {time_delta:.0f}s after event start")

    # Rule 6: Suspicious GPS ping detected (impossible movement speed)
    location_consistent = 0 if had_suspicious_ping else 1
    if had_suspicious_ping:
        score += 30
        flags.append("GPS_SPOOF_DETECTED: Impossible movement speed in location history")

    # ── ML ML Model Inference (Isolation Forest) ─────────────────────────────
    ml_score = 0.0
    if _fraud_model and _scaler:
        try:
            # Match training features: city_match, platform_active, claims_this_week, 
            # time_delta_seconds, active_hours_ratio, claim_amount_ratio, 
            # disruption_type, location_consistent
            features = pd.DataFrame([{
                "city_match": city_match,
                "platform_active": platform_active,
                "claims_this_week": claims_this_week,
                "time_delta_seconds": max(0, time_delta),
                "active_hours_ratio": active_hours_ratio,
                "claim_amount_ratio": claim_amount_ratio,
                "disruption_type": _TYPE_MAP.get(disruption_type, 0),
                "location_consistent": location_consistent,
            }])
            X_scaled = _scaler.transform(features)
            # decision_function returns signed distance from hyperplane; 
            # negative = anomaly, positive = normal
            decision_val = float(_fraud_model.decision_function(X_scaled)[0])
            
            # Convert decision_val to a 0-100 score (higher = more anomalous)
            # Typical decision_val is range [-0.5, 0.5]
            ml_anomaly_score = max(0, min(100, (0.2 - decision_val) * 200))
            if ml_anomaly_score > 60:
                flags.append(f"ML_ANOMALY: Isolation Forest flagged claim (score: {ml_anomaly_score:.1f})")
                ml_score = ml_anomaly_score
        except Exception as e:
            print(f"[ML FRAUD ERROR] {e}")

    # Use max of rule-based and ML-based score
    score = max(score, ml_score)
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
