"""
DSS Engine Service
==================
Unified DSS calculation with 3-level fallback:
  1. XGBoost ML model (trained on 190k real + synthetic rows)
  2. Dynamic formula from raw sensor value (Level 2)
  3. Static lookup table (original behavior — never fails)

Used at disruption detection time (Celery worker) so the DSS is
computed once per event and stored in DisruptionEvent.dss_multiplier.
All downstream code (batch settlement, claims) just reads the stored value.
"""
import os
from typing import Optional
import numpy as np
import joblib
from app.models.models import DisruptionType, DisruptionSeverity

# ── Model loading ─────────────────────────────────────────────────────────────
_DIR = os.path.join(os.path.dirname(__file__), "../../ml/dss_engine")
_MODEL_PATH  = os.path.join(_DIR, "model.joblib")
_SCALER_PATH = os.path.join(_DIR, "scaler.joblib")

try:
    _model  = joblib.load(_MODEL_PATH)
    _scaler = joblib.load(_SCALER_PATH)
    _ml_available = True
except Exception:
    _model = _scaler = None
    _ml_available = False

# Disruption type → integer encoding (must match train.py)
_DTYPE_MAP = {
    DisruptionType.HEAVY_RAIN:         0,
    DisruptionType.EXTREME_HEAT:       1,
    DisruptionType.AQI_SPIKE:          2,
    DisruptionType.TRAFFIC_DISRUPTION: 3,
    DisruptionType.CIVIC_EMERGENCY:    4,
}

# ── Level 3: Static fallback table ───────────────────────────────────────────
_STATIC_TABLE = {
    DisruptionType.HEAVY_RAIN: {
        DisruptionSeverity.MODERATE: 0.30,
        DisruptionSeverity.SEVERE:   0.60,
        DisruptionSeverity.EXTREME:  1.00,
    },
    DisruptionType.EXTREME_HEAT: {
        DisruptionSeverity.MODERATE: 0.30,
        DisruptionSeverity.SEVERE:   0.60,
        DisruptionSeverity.EXTREME:  1.00,
    },
    DisruptionType.AQI_SPIKE: {
        DisruptionSeverity.MODERATE: 0.20,
        DisruptionSeverity.SEVERE:   0.50,
        DisruptionSeverity.EXTREME:  1.00,
    },
    DisruptionType.TRAFFIC_DISRUPTION: {
        DisruptionSeverity.MODERATE: 0.30,
        DisruptionSeverity.SEVERE:   0.50,
        DisruptionSeverity.EXTREME:  0.80,
    },
    DisruptionType.CIVIC_EMERGENCY: {
        DisruptionSeverity.MODERATE: 0.50,
        DisruptionSeverity.SEVERE:   0.80,
        DisruptionSeverity.EXTREME:  1.00,
    },
}


# ── Level 2: Dynamic formula ──────────────────────────────────────────────────

def _dynamic_dss(
    disruption_type: DisruptionType,
    raw_value: float,
    infra_score: float,
    severity: DisruptionSeverity,
) -> float:
    """Continuous DSS from raw sensor value + infra score."""
    infra = float(infra_score or 0.55)
    val   = float(raw_value or 0.0)

    if disruption_type == DisruptionType.HEAVY_RAIN:
        if val <= 0:
            return _static_dss(disruption_type, severity)
        base     = np.clip(np.log1p(val) / np.log1p(100), 0.0, 1.0)
        infra_amp = np.clip(0.85 + (infra - 0.30) * (0.55 / 0.70), 0.85, 1.40)
        return float(np.clip(base * infra_amp, 0.0, 1.0))

    elif disruption_type == DisruptionType.EXTREME_HEAT:
        if val < 38.0:
            return _static_dss(disruption_type, severity)
        base     = np.clip((val - 38.0) / 10.0, 0.0, 1.0)
        heat_amp = np.clip(0.90 + (infra - 0.30) * (0.30 / 0.70), 0.90, 1.20)
        return float(np.clip(base * heat_amp, 0.0, 1.0))

    elif disruption_type == DisruptionType.AQI_SPIKE:
        if val <= 100:
            return _static_dss(disruption_type, severity)
        base    = np.clip((val - 100) / 350.0, 0.0, 1.0)
        aqi_amp = np.clip(0.90 + (infra - 0.30) * (0.25 / 0.70), 0.90, 1.15)
        return float(np.clip(base * aqi_amp, 0.0, 1.0))

    elif disruption_type == DisruptionType.TRAFFIC_DISRUPTION:
        # raw_value = congestion index (0-100)
        if val <= 0:
            return _static_dss(disruption_type, severity)
        base    = np.clip(val / 100.0, 0.0, 1.0)
        amp     = np.clip(0.80 + (infra - 0.30) * (0.40 / 0.70), 0.80, 1.20)
        return float(np.clip(base * amp * 0.90, 0.0, 0.90))

    else:
        return _static_dss(disruption_type, severity)


def _static_dss(disruption_type: DisruptionType, severity: DisruptionSeverity) -> float:
    return _STATIC_TABLE.get(disruption_type, {}).get(severity, 0.30)


# ── Level 1: ML model prediction ─────────────────────────────────────────────

def _ml_dss(
    disruption_type: DisruptionType,
    raw_value: float,
    raw_value2: float,
    infra_score: float,
    col_index: float,
    pop_density: float,
    month: int,
) -> Optional[float]:
    if not _ml_available:
        return None
    try:
        import math
        month_sin = math.sin(2 * math.pi * month / 12)
        month_cos = math.cos(2 * math.pi * month / 12)
        features = [[
            _DTYPE_MAP.get(disruption_type, 0),
            float(raw_value  or 0.0),
            float(raw_value2 or 0.0),
            float(infra_score or 0.55),
            float(col_index  or 1.0),
            float(pop_density or 0.60),
            month_sin,
            month_cos,
        ]]
        scaled = _scaler.transform(features)
        pred   = float(_model.predict(scaled)[0])
        return float(np.clip(pred, 0.0, 1.0))
    except Exception:
        return None


# ── Public API ────────────────────────────────────────────────────────────────

async def calculate_dss(
    disruption_type: DisruptionType,
    severity: DisruptionSeverity,
    city: str = "",
    pincode: str = "",
    raw_value: float = None,
    raw_value2: float = None,
    month: int = None,
) -> dict:
    """
    Calculate DSS for a disruption event.
    Tries ML → dynamic formula → static table in order.
    Returns dict with dss value and which method was used.

    Args:
        disruption_type: DisruptionType enum
        severity:        DisruptionSeverity enum
        city:            city name (used for infra + CoL lookup)
        pincode:         pincode (used for infra lookup)
        raw_value:       primary sensor value (mm rain, temp C, AQI, congestion index)
        raw_value2:      secondary sensor (PM2.5 for AQI, tmax for traffic)
        month:           1-12 (defaults to current month)
    """
    from datetime import datetime
    from app.services.infra_service import get_infra_score

    if month is None:
        month = datetime.now().month

    # Get infra score and CoL for this location
    try:
        infra_score = await get_infra_score(city, pincode)
    except Exception:
        infra_score = 0.55

    try:
        from app.services.platform_service import get_city_economics_async
        col_index, _ = await get_city_economics_async(city)
    except Exception:
        col_index = 1.0

    # Estimate population density from CoL (proxy — denser cities cost more)
    pop_density = float(np.clip((col_index - 0.75) / 0.70, 0.20, 1.0))

    # Level 1: ML model
    ml_result = _ml_dss(
        disruption_type=disruption_type,
        raw_value=raw_value or 0.0,
        raw_value2=raw_value2 or 0.0,
        infra_score=infra_score,
        col_index=col_index,
        pop_density=pop_density,
        month=month,
    )
    if ml_result is not None:
        return {"dss": round(ml_result, 3), "method": "ml", "infra_score": infra_score}

    # Level 2: Dynamic formula
    if raw_value is not None:
        dyn = _dynamic_dss(disruption_type, raw_value, infra_score, severity)
        return {"dss": round(dyn, 3), "method": "dynamic", "infra_score": infra_score}

    # Level 3: Static table
    static = _static_dss(disruption_type, severity)
    return {"dss": round(static, 3), "method": "static", "infra_score": infra_score}
