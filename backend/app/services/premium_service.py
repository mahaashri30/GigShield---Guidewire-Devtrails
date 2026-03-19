"""
AI-Powered Dynamic Premium Calculation Engine
Uses rule-based logic + ML features for Phase 1 (minimal scope)
Full XGBoost model training in Phase 2
"""
from datetime import datetime
from app.models.models import PolicyTier

# Base premiums per tier (₹/week)
BASE_PREMIUMS = {
    PolicyTier.BASIC: 29.0,
    PolicyTier.SMART: 49.0,
    PolicyTier.PRO: 79.0,
}

# Max daily payout per tier (₹)
MAX_DAILY_PAYOUT = {
    PolicyTier.BASIC: 300.0,
    PolicyTier.SMART: 550.0,
    PolicyTier.PRO: 750.0,
}

# Max weekly payout per tier (₹)
MAX_WEEKLY_PAYOUT = {
    PolicyTier.BASIC: 600.0,
    PolicyTier.SMART: 1100.0,
    PolicyTier.PRO: 1500.0,
}

# Zone risk multipliers by pincode prefix (first 3 digits)
# Based on historical disruption frequency
ZONE_RISK = {
    "560": 1.2,  # Bangalore central - flood prone
    "400": 1.35, # Mumbai - high monsoon risk
    "110": 1.15, # Delhi - heat + AQI
    "600": 1.1,  # Chennai - cyclone risk
    "500": 1.05, # Hyderabad - moderate
    "411": 1.1,  # Pune
    "700": 1.05, # Kolkata
}

# Season factors by month
SEASON_FACTORS = {
    1: 1.0,  # Jan
    2: 1.0,  # Feb
    3: 1.05, # Mar - early summer
    4: 1.1,  # Apr
    5: 1.2,  # May - peak heat
    6: 1.3,  # Jun - monsoon starts
    7: 1.35, # Jul - peak monsoon
    8: 1.3,  # Aug
    9: 1.2,  # Sep
    10: 1.05,# Oct
    11: 1.0, # Nov
    12: 1.0, # Dec
}


def get_zone_risk(pincode: str) -> float:
    prefix = pincode[:3] if len(pincode) >= 3 else "000"
    return ZONE_RISK.get(prefix, 1.0)


def get_season_factor() -> float:
    return SEASON_FACTORS.get(datetime.now().month, 1.0)


def calculate_premium(
    tier: PolicyTier,
    pincode: str,
    worker_history_factor: float = 1.0,
    platform_activity_score: float = 1.0,
) -> dict:
    """
    Calculate dynamic weekly premium using risk factors.
    
    Formula:
    Premium = Base × Zone_Risk × Season_Factor × Worker_History × Platform_Activity
    """
    base = BASE_PREMIUMS[tier]
    zone_risk = get_zone_risk(pincode)
    season = get_season_factor()

    adjusted = base * zone_risk * season * worker_history_factor * platform_activity_score
    adjusted = round(adjusted, 2)

    return {
        "tier": tier,
        "base_premium": base,
        "adjusted_premium": adjusted,
        "zone_risk_multiplier": zone_risk,
        "season_factor": season,
        "worker_history_factor": worker_history_factor,
        "platform_activity_score": platform_activity_score,
        "max_daily_payout": MAX_DAILY_PAYOUT[tier],
        "max_weekly_payout": MAX_WEEKLY_PAYOUT[tier],
        "risk_breakdown": {
            "base": base,
            "after_zone": round(base * zone_risk, 2),
            "after_season": round(base * zone_risk * season, 2),
            "final": adjusted,
        },
    }


def calculate_payout(
    worker_daily_avg: float,
    dss_multiplier: float,
    active_hours_ratio: float,
    tier: PolicyTier,
    existing_claims_today: float = 0.0,
) -> dict:
    """
    Calculate payout for a triggered claim.
    
    Formula:
    Payout = Worker_Daily_Avg × DSS × Active_Hours_Ratio
    Capped at tier max daily payout
    """
    raw_payout = worker_daily_avg * dss_multiplier * active_hours_ratio
    cap = MAX_DAILY_PAYOUT[tier]
    remaining_cap = max(0, cap - existing_claims_today)
    final_payout = round(min(raw_payout, remaining_cap), 2)

    return {
        "worker_daily_avg": worker_daily_avg,
        "dss_multiplier": dss_multiplier,
        "active_hours_ratio": active_hours_ratio,
        "raw_payout": round(raw_payout, 2),
        "tier_cap": cap,
        "approved_amount": final_payout,
        "capped": raw_payout > cap,
    }
