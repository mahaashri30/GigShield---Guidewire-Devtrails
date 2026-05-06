"""
Platform Earnings Service — Mock (Phase 1)

Simulates what a real platform partner API would return when queried
by a delivery worker's registered phone number.

Real integration (Phase 2):
  - Blinkit  : GET https://partner-api.blinkit.com/v1/earnings?phone={phone}
  - Zepto    : GET https://partner.zepto.co/api/earnings?phone={phone}
  - Swiggy   : GET https://partner.swiggy.com/api/v1/worker/earnings?phone={phone}
  - Zomato   : GET https://hyperpure.zomato.com/partner/api/earnings?phone={phone}
  - Amazon   : GET https://flex.amazon.in/api/earnings?phone={phone}
  - BigBasket: GET https://partner.bigbasket.com/api/earnings?phone={phone}

Each platform returns a weekly settlement summary from which we derive
avg_daily_earnings = weekly_settlement / active_days_in_week.

Per README persona (Arun Kumar, quick-commerce grocery delivery):
  Earnings: ₹800–₹1,200/day  |  ₹5,600–₹8,400/week
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
    "Mumbai":          (1.45, 0.58),
    "Delhi":           (1.35, 0.52),
    "Bangalore":       (1.30, 0.53),
    "Chennai":         (1.20, 0.50),
    "Hyderabad":       (1.15, 0.48),
    "Pune":            (1.15, 0.48),
    "Kolkata":         (1.10, 0.50),
    "Noida":           (1.25, 0.51),
    "Gurgaon":         (1.30, 0.52),
    "Ahmedabad":       (1.05, 0.44),
    "Surat":           (1.05, 0.43),
    "Jaipur":          (1.00, 0.42),
    "Lucknow":         (0.95, 0.42),
    "Indore":          (0.95, 0.41),
    "Bhopal":          (0.90, 0.40),
    "Nagpur":          (0.95, 0.41),
    "Coimbatore":      (1.00, 0.40),
    "Madurai":         (0.90, 0.38),
    "Tiruchirappalli": (0.88, 0.38),
    "Kochi":           (1.05, 0.45),
    "Chandigarh":      (1.10, 0.46),
    "Visakhapatnam":   (0.95, 0.41),
    "Vadodara":        (0.95, 0.41),
    "Amritsar":        (0.90, 0.40),
    "Ludhiana":        (0.92, 0.40),
    "Patna":           (0.75, 0.36),
    "Guwahati":        (0.80, 0.37),
    "Ranchi":          (0.78, 0.36),
    "Varanasi":        (0.80, 0.37),
    "Agra":            (0.82, 0.38),
    "Meerut":          (0.85, 0.38),
    "Gorakhpur":       (0.75, 0.35),
    "Siliguri":        (0.80, 0.37),
}

DEFAULT_COL = 1.0
DEFAULT_SUBSISTENCE = 0.42

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
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

    async with httpx.AsyncClient(timeout=8.0) as client:
        res = await client.post(
            f"{_GEMINI_URL}?key={settings.GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 100},
            },
        )
        data = res.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)
        col = float(parsed["col_index"])
        sub = float(parsed["subsistence_ratio"])
        return round(max(0.70, min(1.50, col)), 2), round(max(0.35, min(0.60, sub)), 2)


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
    "blinkit": {
        "range": (850, 1200),   # 10-min delivery, high order density
        "active_days": (5, 7),
        "label": "Blinkit",
    },
    "zepto": {
        "range": (800, 1150),   # Similar to Blinkit
        "active_days": (5, 7),
        "label": "Zepto",
    },
    "swiggy_instamart": {
        "range": (780, 1100),   # Instamart grocery delivery
        "active_days": (5, 6),
        "label": "Swiggy Instamart",
    },
    "zomato": {
        "range": (700, 1050),   # Food delivery, peak hours dependent
        "active_days": (5, 7),
        "label": "Zomato",
    },
    "amazon": {
        "range": (750, 1000),   # Amazon Flex, scheduled blocks
        "active_days": (4, 6),
        "label": "Amazon",
    },
    "bigbasket": {
        "range": (650, 950),    # Scheduled grocery delivery, lower density
        "active_days": (5, 6),
        "label": "BigBasket",
    },
}

DEFAULT_EARNINGS = 700.0


async def fetch_platform_activity(
    phone: str,
    platform: str,
    window_start: "datetime",
    window_end: "datetime",
) -> dict:
    """
    Mock platform activity API — simulates whether a worker was online
    on their delivery platform during a given time window.

    Real integration (Phase 2):
      Blinkit/Zepto/Swiggy would return session logs showing when the
      worker had the app open and was accepting orders.

    Mock logic (deterministic per phone+platform+hour):
      - Workers are online ~70% of active hours (6am-10pm)
      - Seed is phone+platform so same worker always gets same pattern
      - Returns online_minutes and activity_ratio for the window
    """
    import asyncio
    from datetime import timezone
    await asyncio.sleep(0.05)  # simulate network latency

    seed = int("".join(filter(str.isdigit, phone))[-6:] or "123456")
    rng = random.Random(seed + hash(platform) % 10000)

    # Calculate window duration in minutes
    if window_start.tzinfo is None:
        window_start = window_start.replace(tzinfo=timezone.utc)
    if window_end.tzinfo is None:
        window_end = window_end.replace(tzinfo=timezone.utc)

    total_minutes = max(1, int((window_end - window_start).total_seconds() / 60))

    # Mock: worker was online for 60-85% of the window
    activity_ratio = round(rng.uniform(0.60, 0.85), 3)
    online_minutes = int(total_minutes * activity_ratio)

    # Simulate occasional fully-offline workers (10% chance — device off / not working)
    if rng.random() < 0.10:
        activity_ratio = 0.0
        online_minutes = 0

    return {
        "phone": phone,
        "platform": platform,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "total_window_minutes": total_minutes,
        "online_minutes": online_minutes,
        "activity_ratio": activity_ratio,
        "was_active": activity_ratio > 0.0,
        "source": f"{platform.capitalize()} Partner API (mock)",
    }

async def fetch_platform_earnings(phone: str, platform: str, city: str = "") -> dict:
    """
    Mock platform API call — returns avg daily earnings for a worker.
    Earnings are adjusted by city Cost of Living index.
    Mumbai Blinkit rider earns ~45% more than Jaipur Blinkit rider.
    """
    await asyncio.sleep(0.3)

    config = PLATFORM_EARNINGS.get(platform)
    col = get_col_index(city) if city else DEFAULT_COL

    if not config:
        base = round(DEFAULT_EARNINGS * col, 2)
        return {
            "platform": platform,
            "phone": phone,
            "city": city,
            "avg_daily_earnings": base,
            "weekly_settlement": round(base * 6, 2),
            "active_days_last_week": 6,
            "col_index": col,
            "source": "default",
            "verified": False,
        }

    seed = int("".join(filter(str.isdigit, phone))[-6:] or "123456")
    rng = random.Random(seed + hash(platform) % 10000)

    low, high = config["range"]
    # Apply CoL multiplier to earnings range
    avg_daily = round(rng.uniform(low, high) * col, 2)

    day_low, day_high = config["active_days"]
    active_days_week = rng.randint(day_low, day_high)
    active_days_30 = rng.randint(active_days_week * 3, active_days_week * 4)
    weekly_settlement = round(avg_daily * active_days_week, 2)

    return {
        "platform": platform,
        "platform_label": config["label"],
        "phone": phone,
        "city": city,
        "avg_daily_earnings": avg_daily,
        "weekly_settlement": weekly_settlement,
        "active_days_last_week": active_days_week,
        "active_days_30": active_days_30,
        "col_index": col,
        "source": f"{config['label']} Partner API (mock)",
        "verified": True,
    }
