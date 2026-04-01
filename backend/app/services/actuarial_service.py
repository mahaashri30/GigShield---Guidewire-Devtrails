"""
Actuarial Engine for GigShield
Implements:
- BCR (Burning Cost Rate) = total claims / total premium collected
- Loss Ratio monitoring with auto-suspension at >85%
- Actuarial base premium: trigger_probability × avg_income_lost × days_exposed
- Stress scenario: 14-day monsoon simulation
"""
from app.models.models import PolicyTier

# ── Historical trigger probabilities per city per peril (10-year IMD/CPCB data) ──
# P(trigger) = days per year where threshold is breached / 365
TRIGGER_PROBABILITY = {
    "Delhi": {
        "heavy_rain":         0.04,  # ~15 days/year above 35mm/hr
        "extreme_heat":       0.12,  # ~44 days/year above 42C
        "aqi_spike":          0.18,  # ~66 days/year AQI>200
        "traffic_disruption": 0.08,
        "civic_emergency":    0.03,
    },
    "Mumbai": {
        "heavy_rain":         0.14,  # ~51 days/year (monsoon city)
        "extreme_heat":       0.02,
        "aqi_spike":          0.06,
        "traffic_disruption": 0.10,
        "civic_emergency":    0.04,
    },
    "Bangalore": {
        "heavy_rain":         0.12,
        "extreme_heat":       0.02,
        "aqi_spike":          0.05,
        "traffic_disruption": 0.09,
        "civic_emergency":    0.04,
    },
    "Chennai": {
        "heavy_rain":         0.10,
        "extreme_heat":       0.06,
        "aqi_spike":          0.04,
        "traffic_disruption": 0.06,
        "civic_emergency":    0.03,
    },
    "Hyderabad": {
        "heavy_rain":         0.08,
        "extreme_heat":       0.07,
        "aqi_spike":          0.05,
        "traffic_disruption": 0.07,
        "civic_emergency":    0.03,
    },
}

DEFAULT_TRIGGER_PROB = {
    "heavy_rain": 0.08, "extreme_heat": 0.06, "aqi_spike": 0.07,
    "traffic_disruption": 0.07, "civic_emergency": 0.03,
}

# DSS per peril (avg income loss fraction when triggered)
AVG_DSS = {
    "heavy_rain": 0.55, "extreme_heat": 0.55, "aqi_spike": 0.40,
    "traffic_disruption": 0.40, "civic_emergency": 0.65,
}

# Target BCR range (65 paise per ₹1 goes to payouts)
TARGET_BCR_MIN = 0.55
TARGET_BCR_MAX = 0.70
LOSS_RATIO_SUSPEND_THRESHOLD = 0.85  # suspend new enrolments above this

# Tier coverage: which perils each tier covers
TIER_PERILS = {
    PolicyTier.BASIC: ["heavy_rain"],
    PolicyTier.SMART: ["heavy_rain", "extreme_heat", "aqi_spike"],
    PolicyTier.PRO:   ["heavy_rain", "extreme_heat", "aqi_spike", "traffic_disruption", "civic_emergency"],
}


def calculate_actuarial_premium(
    tier: PolicyTier,
    city: str,
    avg_daily_earnings: float,
    days_exposed: int = 7,
    safety_loading: float = 1.35,  # 35% loading for expenses + profit
) -> dict:
    """
    Actuarial base premium formula:
    Premium = sum over perils of [P(trigger) × avg_income_lost × days_exposed] × safety_loading

    This is the pure risk premium — what it actually costs to cover the worker.
    safety_loading covers: expenses (15%) + profit margin (10%) + reserve (10%)
    """
    perils = TIER_PERILS[tier]
    city_probs = TRIGGER_PROBABILITY.get(city, DEFAULT_TRIGGER_PROB)

    pure_risk_premium = 0.0
    peril_breakdown = {}

    for peril in perils:
        p_trigger = city_probs.get(peril, DEFAULT_TRIGGER_PROB.get(peril, 0.05))
        avg_dss = AVG_DSS.get(peril, 0.5)
        avg_income_lost = avg_daily_earnings * avg_dss
        peril_premium = p_trigger * avg_income_lost * days_exposed
        pure_risk_premium += peril_premium
        peril_breakdown[peril] = {
            "trigger_probability": round(p_trigger, 3),
            "avg_income_lost_per_day": round(avg_income_lost, 2),
            "days_exposed": days_exposed,
            "peril_premium": round(peril_premium, 2),
        }

    loaded_premium = round(pure_risk_premium * safety_loading, 2)

    return {
        "tier": tier,
        "city": city,
        "avg_daily_earnings": avg_daily_earnings,
        "pure_risk_premium": round(pure_risk_premium, 2),
        "safety_loading": safety_loading,
        "actuarial_premium": loaded_premium,
        "peril_breakdown": peril_breakdown,
        "formula": "sum[P(trigger) x avg_income_lost x days_exposed] x safety_loading",
    }


def calculate_bcr(total_claims_paid: float, total_premium_collected: float) -> dict:
    """
    BCR = total claims paid / total premium collected
    Target: 0.55-0.70 (65 paise per ₹1 goes to payouts)
    """
    if total_premium_collected <= 0:
        return {"bcr": 0.0, "status": "insufficient_data", "action": "none"}

    bcr = round(total_claims_paid / total_premium_collected, 4)

    if bcr > LOSS_RATIO_SUSPEND_THRESHOLD:
        status = "critical"
        action = "suspend_new_enrolments"
    elif bcr > TARGET_BCR_MAX:
        status = "elevated"
        action = "increase_premium_next_cycle"
    elif bcr < TARGET_BCR_MIN:
        status = "low"
        action = "consider_premium_reduction"
    else:
        status = "healthy"
        action = "maintain"

    return {
        "bcr": bcr,
        "total_claims_paid": total_claims_paid,
        "total_premium_collected": total_premium_collected,
        "target_range": f"{TARGET_BCR_MIN}-{TARGET_BCR_MAX}",
        "status": status,
        "action": action,
        "paise_per_rupee": round(bcr * 100, 1),
    }


def stress_test_monsoon(
    city: str,
    avg_daily_earnings: float,
    tier: PolicyTier,
    monsoon_days: int = 14,
) -> dict:
    """
    Stress scenario: 14-day continuous monsoon.
    Models worst-case payout liability per worker.
    """
    from app.services.premium_service import MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT

    city_probs = TRIGGER_PROBABILITY.get(city, DEFAULT_TRIGGER_PROB)
    rain_prob = city_probs.get("heavy_rain", 0.08)

    # During monsoon, trigger probability spikes to ~80% daily
    monsoon_trigger_prob = min(rain_prob * 8, 0.85)
    avg_dss = 0.70  # severe rain during monsoon
    daily_income_loss = avg_daily_earnings * avg_dss

    expected_trigger_days = round(monsoon_days * monsoon_trigger_prob, 1)
    expected_total_loss = round(expected_trigger_days * daily_income_loss, 2)

    # Cap at weekly limits (2 weeks = 2 weekly caps)
    weekly_cap = MAX_WEEKLY_PAYOUT[tier]
    max_liability_per_worker = weekly_cap * 2
    capped_liability = min(expected_total_loss, max_liability_per_worker)

    weekly_premium = MAX_DAILY_PAYOUT[tier] * 0.08  # approx premium
    premium_collected_14d = weekly_premium * 2
    stress_bcr = round(capped_liability / max(premium_collected_14d, 1), 2)

    return {
        "scenario": "14-day monsoon stress test",
        "city": city,
        "tier": tier,
        "monsoon_days": monsoon_days,
        "monsoon_trigger_probability": monsoon_trigger_prob,
        "expected_trigger_days": expected_trigger_days,
        "daily_income_loss": round(daily_income_loss, 2),
        "expected_total_loss": expected_total_loss,
        "max_liability_per_worker": max_liability_per_worker,
        "capped_liability": capped_liability,
        "stress_bcr": stress_bcr,
        "verdict": "SOLVENT" if stress_bcr < 1.5 else "RESERVE_REQUIRED",
    }
