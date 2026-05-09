"""
Platform Earnings Service

Phase 1 (current): Worker self-reported baseline + GPS ping proxy.
  - Worker enters avg_daily_earnings, avg_online_hours, avg_orders_per_day at registration
  - 15-20 day rolling baseline computed from our own GPS activity data
  - order_drop_ratio estimated from DSS + disruption type (no platform API needed)

Phase 2 (B2B agreement required):
  Formal data-sharing agreement with Blinkit/Zepto/Swiggy needed to access:
  - Per-order timestamps (accepted_at, delivered_at)
  - Per-hour earnings breakdown
  - Online vs active session logs
  None of these platforms have a public partner API for third-party access.
  Integration path: ONDC framework or direct B2B MOU with platform.

Baseline calculation (Phase 1):
  Uses last 15 active working days of the worker to compute:
  - avg_hourly_earnings  = avg_daily_earnings / avg_online_hours
  - avg_orders_per_hour  = avg_orders_per_day / avg_online_hours
  - normal_earnings_in_window = avg_hourly_earnings x disruption_duration_hours
  Then compares against estimated actual earnings during disruption
  using DSS-based order drop model.
"""
import random
import asyncio
import json
import hashlib
import httpx
from typing import Optional
from app.config import settings


# Cost of Living index AND subsistence ratio per city
# col_index: relative cost of living (1.0 = Tier-2 base)
# subsistence_ratio: minimum daily spend / typical daily earnings
#   Higher ratio = more of income goes to survival = disruption hurts more relatively
CITY_ECONOMICS = {
    # city: (col_index, subsistence_ratio)
    # Metros
    "Mumbai":          (1.45, 0.58),
    "Delhi":           (1.35, 0.52),
    "Bangalore":       (1.30, 0.53),
    "Chennai":         (1.20, 0.50),
    "Hyderabad":       (1.15, 0.48),
    "Pune":            (1.15, 0.48),
    "Kolkata":         (1.10, 0.50),
    "Noida":           (1.25, 0.51),
    "Gurgaon":         (1.30, 0.52),
    "Faridabad":       (1.10, 0.46),
    "Kanpur":          (0.88, 0.40),
    # Large cities
    "Ahmedabad":       (1.05, 0.44),
    "Surat":           (1.05, 0.43),
    "Jaipur":          (1.00, 0.42),
    "Lucknow":         (0.95, 0.42),
    "Indore":          (0.95, 0.41),
    "Bhopal":          (0.90, 0.40),
    "Nagpur":          (0.95, 0.41),
    "Chandigarh":      (1.10, 0.46),
    "Visakhapatnam":   (0.95, 0.41),
    "Vadodara":        (0.95, 0.41),
    "Kochi":           (1.05, 0.45),
    "Dehradun":        (0.95, 0.41),
    # Mid-size cities
    "Coimbatore":      (1.00, 0.40),
    "Madurai":         (0.90, 0.38),
    "Tiruchirappalli": (0.88, 0.38),
    "Salem":           (0.85, 0.38),
    "Erode":           (0.83, 0.37),
    "Amritsar":        (0.90, 0.40),
    "Ludhiana":        (0.92, 0.40),
    "Mysore":          (1.00, 0.41),
    "Hubli":           (0.88, 0.39),
    "Mangalore":       (0.95, 0.41),
    "Nashik":          (0.95, 0.41),
    "Aurangabad":      (0.90, 0.40),
    "Jodhpur":         (0.88, 0.39),
    "Raipur":          (0.85, 0.38),
    "Bhubaneswar":     (0.88, 0.39),
    "Vijayawada":      (0.90, 0.40),
    "Warangal":        (0.85, 0.38),
    "Guntur":          (0.85, 0.38),
    "Rajkot":          (0.92, 0.40),
    "Jabalpur":        (0.85, 0.38),
    "Gwalior":         (0.85, 0.38),
    # Smaller cities
    "Patna":           (0.75, 0.36),
    "Guwahati":        (0.80, 0.37),
    "Ranchi":          (0.78, 0.36),
    "Varanasi":        (0.80, 0.37),
    "Agra":            (0.82, 0.38),
    "Meerut":          (0.85, 0.38),
    "Gorakhpur":       (0.75, 0.35),
    "Siliguri":        (0.80, 0.37),
    "Imphal":          (0.72, 0.34),
    "Shillong":        (0.75, 0.35),
    "Gaya":            (0.72, 0.34),
    "Dhanbad":         (0.75, 0.35),
    "Rourkela":        (0.78, 0.36),
}

DEFAULT_COL = 1.0
DEFAULT_SUBSISTENCE = 0.42

_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_col_cache: dict[str, tuple[float, float]] = {}


def _col_cache_key(city: str) -> str:
    return hashlib.md5(city.lower().encode()).hexdigest()[:8]


async def _ai_col(city: str) -> tuple[float, float]:
    prompt = f"""You are an insurance actuary estimating cost of living for Indian cities.

City: {city}, India

Return ONLY a JSON object:
{{"col_index": 0.XX, "subsistence_ratio": 0.XX, "reason": "one-line reason"}}

col_index guide (relative to Tier-2 base = 1.0):
- 1.30-1.50: Metro (Mumbai, Delhi, Bangalore)
- 1.10-1.29: Large city (Hyderabad, Chennai, Pune)
- 0.90-1.09: Mid-size city (Jaipur, Lucknow, Coimbatore)
- 0.75-0.89: Smaller city (Patna, Guwahati, Varanasi)

subsistence_ratio: fraction of daily earnings spent on survival needs (0.35-0.60)"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 100},
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        for model in _GEMINI_MODELS:
            url = _GEMINI_BASE.format(model=model) + f"?key={settings.GEMINI_API_KEY}"
            res = await client.post(url, json=payload)
            data = res.json()
            if "candidates" not in data:
                continue
            content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            content = content.replace("```json", "").replace("```", "").strip()
            # Extract JSON object robustly
            start, end = content.find("{"), content.rfind("}")
            if start == -1 or end == -1:
                continue
            parsed = json.loads(content[start:end + 1])
            col = float(parsed["col_index"])
            sub = float(parsed["subsistence_ratio"])
            return round(max(0.70, min(1.50, col)), 2), round(max(0.35, min(0.60, sub)), 2)
    raise ValueError("All Gemini models unavailable")


async def get_city_economics_async(city: str) -> tuple[float, float]:
    """Returns (col_index, subsistence_ratio) — checks static table first, then Gemini AI."""
    # 1. Static lookup
    for known, vals in CITY_ECONOMICS.items():
        if known.lower() in city.lower() or city.lower() in known.lower():
            return vals

    # 2. In-memory cache
    key = _col_cache_key(city)
    if key in _col_cache:
        return _col_cache[key]

    # 3. Gemini AI
    try:
        result = await _ai_col(city)
        _col_cache[key] = result
        print(f"[CoL AI] {city} → col={result[0]}, subsistence={result[1]}")
        return result
    except Exception as e:
        print(f"[CoL AI ERROR] {city}: {e}")

    # 4. Default fallback
    return DEFAULT_COL, DEFAULT_SUBSISTENCE


def get_city_economics(city: str) -> tuple[float, float]:
    """Sync version — static lookup only. Use get_city_economics_async in async contexts."""
    for known, vals in CITY_ECONOMICS.items():
        if known.lower() in city.lower() or city.lower() in known.lower():
            return vals
    return DEFAULT_COL, DEFAULT_SUBSISTENCE


def get_col_index(city: str) -> float:
    return get_city_economics(city)[0]


# Realistic daily earnings ranges per platform (min, max) in ₹
# Based on Tier-2 city average — multiplied by CoL index at runtime
PLATFORM_EARNINGS = {
    # platform: (earnings_range, active_days, online_hours_range, orders_per_day_range)
    # online_hours = time logged into app (online mode)
    # orders_per_day = accepted + completed deliveries (active mode)
    # Quick-commerce (Blinkit/Zepto): short 10-min runs, high order count
    # Food delivery (Zomato/Swiggy): longer runs, fewer orders
    "blinkit": {
        "range": (850, 1200),
        "active_days": (5, 7),
        "online_hours": (8.0, 11.0),   # logged in 8-11h/day
        "orders_per_day": (20, 30),     # 20-30 short runs/day (10-min delivery)
        "label": "Blinkit",
    },
    "zepto": {
        "range": (800, 1150),
        "active_days": (5, 7),
        "online_hours": (8.0, 10.5),
        "orders_per_day": (18, 28),
        "label": "Zepto",
    },
    "swiggy_instamart": {
        "range": (780, 1100),
        "active_days": (5, 6),
        "online_hours": (7.5, 10.0),
        "orders_per_day": (15, 24),
        "label": "Swiggy Instamart",
    },
    "zomato": {
        "range": (700, 1050),
        "active_days": (5, 7),
        "online_hours": (7.0, 10.0),   # food delivery, peak hours
        "orders_per_day": (12, 20),     # fewer but longer runs
        "label": "Zomato",
    },
    "amazon": {
        "range": (750, 1000),
        "active_days": (4, 6),
        "online_hours": (6.0, 9.0),    # scheduled blocks
        "orders_per_day": (10, 18),
        "label": "Amazon",
    },
    "bigbasket": {
        "range": (650, 950),
        "active_days": (5, 6),
        "online_hours": (6.0, 8.5),
        "orders_per_day": (8, 15),     # scheduled grocery, fewer runs
        "label": "BigBasket",
    },
}

DEFAULT_EARNINGS = 700.0
# Default platform activity assumptions (used when worker hasn't set these)
DEFAULT_ONLINE_HOURS_PER_DAY = 9.0    # hours worker is logged into platform
DEFAULT_ORDERS_PER_DAY = 18.0         # orders completed on a normal day

# Order drop % during disruption by type and severity
# Based on real-world delivery platform data patterns:
# Heavy rain = customers order MORE food but roads slow = fewer completions
# Extreme heat = customers order more cold drinks but workers slow down
# AQI = workers avoid going out, order volume drops
# Traffic = roads blocked, completion rate drops sharply
# Civic = full shutdown in affected areas
ORDER_DROP_RATE = {
    "heavy_rain": {
        "moderate": 0.20,  # 20% fewer orders completed
        "severe":   0.45,  # 45% fewer
        "extreme":  0.75,  # 75% fewer — roads flooded
    },
    "extreme_heat": {
        "moderate": 0.10,
        "severe":   0.25,
        "extreme":  0.50,
    },
    "aqi_spike": {
        "moderate": 0.10,
        "severe":   0.30,
        "extreme":  0.55,
    },
    "traffic_disruption": {
        "moderate": 0.25,
        "severe":   0.50,
        "extreme":  0.70,
    },
    "civic_emergency": {
        "moderate": 0.40,
        "severe":   0.70,
        "extreme":  0.95,
    },
}


async def get_worker_baseline(
    worker_id: str,
    db,
    avg_daily_earnings: float,
    avg_online_hours: float = DEFAULT_ONLINE_HOURS_PER_DAY,
    avg_orders_per_day: float = DEFAULT_ORDERS_PER_DAY,
    days: int = 15,
) -> dict:
    """
    Compute worker's normal hourly baseline from last N active working days.

    Uses GPS ping activity as proxy for online hours:
      - Each ping covers a 10-min window
      - A day with >= 3 pings = worker was out delivering that day
      - total_pings x 10min / active_days = estimated online hours/day

    Falls back to worker's self-reported avg_online_hours if GPS data is sparse.

    Phase 2: Replace GPS proxy with actual platform session logs.
    """
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, func, cast, Date
    from app.models.models import WorkerLocationPing

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    day_col = cast(WorkerLocationPing.recorded_at, Date)
    result = await db.execute(
        select(
            day_col.label('day'),
            func.count(WorkerLocationPing.id).label('ping_count'),
        ).where(
            WorkerLocationPing.worker_id == worker_id,
            WorkerLocationPing.recorded_at >= since,
            WorkerLocationPing.is_suspicious == False,
        ).group_by(day_col)
    )
    daily_pings = result.all()
    active_days = sum(1 for row in daily_pings if row.ping_count >= 3)
    total_pings = sum(row.ping_count for row in daily_pings if row.ping_count >= 3)

    # Refine online hours from GPS if we have enough data (5+ active days)
    if active_days >= 5:
        gps_online_hours = round((total_pings * 10 / 60) / active_days, 2)
        # Blend GPS estimate with self-reported (GPS is proxy, not exact)
        # Weight: 60% GPS, 40% self-reported
        estimated_online_hours = round(
            max(4.0, min(14.0, gps_online_hours * 0.6 + avg_online_hours * 0.4)), 2
        )
        data_source = "gps_proxy_blended"
    else:
        # Not enough GPS data — use self-reported value
        estimated_online_hours = avg_online_hours
        data_source = "self_reported"

    avg_hourly_earnings = round(avg_daily_earnings / estimated_online_hours, 2)
    avg_orders_per_hour = round(avg_orders_per_day / estimated_online_hours, 2)

    return {
        "avg_daily_earnings":        avg_daily_earnings,
        "avg_online_hours_per_day":  estimated_online_hours,
        "avg_hourly_earnings":       avg_hourly_earnings,
        "avg_orders_per_hour":       avg_orders_per_hour,
        "avg_orders_per_day":        avg_orders_per_day,
        "active_days_in_window":     active_days,
        "baseline_days":             days,
        "data_source":               data_source,
    }


def compute_income_loss(
    baseline: dict,
    disruption_type: str,
    severity: str,
    disruption_hours: float,
) -> dict:
    """
    Compute actual income loss during disruption using:
      1. Worker's normal hourly earnings (from 15-day baseline)
      2. Order drop rate for this disruption type + severity
      3. Actual disruption duration

    Formula:
      normal_earnings_in_window = avg_hourly_earnings x disruption_hours
      order_drop = ORDER_DROP_RATE[type][severity]
      estimated_actual_earnings = normal_earnings_in_window x (1 - order_drop)
      income_loss = normal_earnings_in_window - estimated_actual_earnings
      income_loss_ratio = income_loss / normal_earnings_in_window

    Example:
      Worker earns Rs.100/hr normally
      Severe heavy rain for 3 hours
      order_drop = 0.45
      normal_in_window = 100 x 3 = Rs.300
      actual_in_window = 300 x (1 - 0.45) = Rs.165
      income_loss = Rs.135
      income_loss_ratio = 0.45
    """
    drop_rate = ORDER_DROP_RATE.get(disruption_type, {}).get(severity, 0.30)

    normal_earnings = round(baseline["avg_hourly_earnings"] * disruption_hours, 2)
    actual_earnings = round(normal_earnings * (1 - drop_rate), 2)
    income_loss = round(normal_earnings - actual_earnings, 2)
    income_loss_ratio = drop_rate  # = 1 - (actual/normal)

    return {
        "disruption_type":       disruption_type,
        "severity":              severity,
        "disruption_hours":      disruption_hours,
        "normal_earnings":       normal_earnings,
        "actual_earnings":       actual_earnings,
        "income_loss":           income_loss,
        "income_loss_ratio":     income_loss_ratio,
        "order_drop_rate":       drop_rate,
        "avg_hourly_earnings":   baseline["avg_hourly_earnings"],
        "baseline_days_used":    baseline["active_days_in_window"],
    }


async def fetch_platform_activity(
    phone: str,
    platform: str,
    window_start: "datetime",
    window_end: "datetime",
) -> dict:
    """
    Mock platform activity API — returns delivery activity during a disruption window.

    Real integration (Phase 2):
      Blinkit/Zepto/Swiggy return per-order timestamps so we know exactly
      how many orders the worker accepted+completed during the disruption.

    Three worker states during disruption:
      1. STOPPED  — activity_ratio=0.0, orders=0       → full income loss
      2. REDUCED  — activity_ratio=0.3-0.6, orders low → partial income loss
      3. NORMAL   — activity_ratio=0.8+, orders normal → minimal/no loss

    Mock logic (deterministic per phone+platform+disruption_hour):
      - 30% chance worker stopped completely (flood/severe disruption)
      - 50% chance worker kept working but got fewer orders (reduced demand)
      - 20% chance worker worked normally (mild disruption, resilient area)
    """
    from datetime import timezone
    await asyncio.sleep(0.05)

    seed = int("".join(filter(str.isdigit, phone))[-6:] or "123456")
    rng = random.Random(seed + hash(platform) % 10000)

    if window_start.tzinfo is None:
        window_start = window_start.replace(tzinfo=timezone.utc)
    if window_end.tzinfo is None:
        window_end = window_end.replace(tzinfo=timezone.utc)

    total_minutes = max(1, int((window_end - window_start).total_seconds() / 60))
    normal_orders_per_hour = {"blinkit": 4.5, "zepto": 4.0, "swiggy_instamart": 3.5,
                              "zomato": 3.0, "amazon": 2.0, "bigbasket": 2.5}.get(platform, 3.0)
    expected_orders = round(normal_orders_per_hour * total_minutes / 60, 1)

    roll = rng.random()
    if roll < 0.30:
        # Stopped completely
        activity_ratio = 0.0
        orders_completed = 0
        earnings_during = 0.0
        worker_state = "stopped"
    elif roll < 0.80:
        # Reduced — working but fewer orders due to low demand / slow roads
        activity_ratio = round(rng.uniform(0.25, 0.65), 3)
        orders_completed = max(0, int(expected_orders * activity_ratio))
        earnings_during = round(orders_completed * rng.uniform(45, 75), 2)
        worker_state = "reduced"
    else:
        # Normal — disruption didn't affect this worker much
        activity_ratio = round(rng.uniform(0.80, 1.0), 3)
        orders_completed = max(1, int(expected_orders * activity_ratio))
        earnings_during = round(orders_completed * rng.uniform(55, 80), 2)
        worker_state = "normal"

    return {
        "phone": phone,
        "platform": platform,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "total_window_minutes": total_minutes,
        "activity_ratio": activity_ratio,
        "orders_completed": orders_completed,
        "earnings_during_window": earnings_during,
        "expected_orders": expected_orders,
        "worker_state": worker_state,
        "was_active": activity_ratio > 0.0,
        "source": f"{platform.capitalize()} Partner API (mock)",
    }

async def fetch_platform_earnings(phone: str, platform: str, city: str = "") -> dict:
    """
    Mock platform earnings — returns avg daily earnings, online hours,
    and orders per day for a worker based on their platform.

    Online hours  = time worker is logged into the platform app (online mode)
    Orders per day = accepted + completed deliveries (active mode)

    Phase 2: Replace with actual B2B partner API call.
    """
    await asyncio.sleep(0.3)

    config = PLATFORM_EARNINGS.get(platform)
    col = get_col_index(city) if city else DEFAULT_COL

    seed = int("".join(filter(str.isdigit, phone))[-6:] or "123456")
    rng = random.Random(seed + hash(platform) % 10000)

    if not config:
        base = round(DEFAULT_EARNINGS * col, 2)
        return {
            "platform": platform,
            "phone": phone,
            "city": city,
            "avg_daily_earnings": base,
            "avg_online_hours_per_day": DEFAULT_ONLINE_HOURS_PER_DAY,
            "avg_orders_per_day": DEFAULT_ORDERS_PER_DAY,
            "weekly_settlement": round(base * 6, 2),
            "active_days_last_week": 6,
            "active_days_30": 22,
            "col_index": col,
            "source": "default",
            "verified": False,
        }

    low, high = config["range"]
    avg_daily = round(rng.uniform(low, high) * col, 2)

    day_low, day_high = config["active_days"]
    active_days_week = rng.randint(day_low, day_high)
    active_days_30 = rng.randint(active_days_week * 3, active_days_week * 4)
    weekly_settlement = round(avg_daily * active_days_week, 2)

    # Online hours and orders — deterministic per worker phone+platform
    oh_low, oh_high = config["online_hours"]
    avg_online_hours = round(rng.uniform(oh_low, oh_high), 1)

    ord_low, ord_high = config["orders_per_day"]
    avg_orders = round(rng.uniform(ord_low, ord_high), 1)

    return {
        "platform": platform,
        "platform_label": config["label"],
        "phone": phone,
        "city": city,
        "avg_daily_earnings": avg_daily,
        "avg_online_hours_per_day": avg_online_hours,
        "avg_orders_per_day": avg_orders,
        "weekly_settlement": weekly_settlement,
        "active_days_last_week": active_days_week,
        "active_days_30": active_days_30,
        "col_index": col,
        "source": f"{config['label']} Partner API (mock)",
        "verified": True,
    }
