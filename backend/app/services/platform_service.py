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
from typing import Optional


# Realistic daily earnings ranges per platform (min, max) in ₹
# Based on publicly reported gig worker earnings in India (2024-25)
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


async def fetch_platform_earnings(phone: str, platform: str) -> dict:
    """
    Mock platform API call — returns avg daily earnings for a worker
    identified by their registered phone number.

    In Phase 2 this becomes a real HTTP call to the platform partner API.
    The phone number is the key used by all platforms to identify their
    delivery partners (same number used for OTP login on their apps).
    """
    # Simulate network latency of a real API call
    await asyncio.sleep(0.3)

    config = PLATFORM_EARNINGS.get(platform)
    if not config:
        return {
            "platform": platform,
            "phone": phone,
            "avg_daily_earnings": DEFAULT_EARNINGS,
            "weekly_settlement": round(DEFAULT_EARNINGS * 6, 2),
            "active_days_last_week": 6,
            "source": "default",
            "verified": False,
        }

    # Seed random with phone + platform so the same worker always gets
    # the same earnings (deterministic mock — consistent across restarts)
    seed = int("".join(filter(str.isdigit, phone))[-6:] or "123456")
    rng = random.Random(seed + hash(platform) % 10000)

    low, high = config["range"]
    avg_daily = round(rng.uniform(low, high), 2)

    day_low, day_high = config["active_days"]
    active_days = rng.randint(day_low, day_high)
    weekly_settlement = round(avg_daily * active_days, 2)

    return {
        "platform": platform,
        "platform_label": config["label"],
        "phone": phone,
        "avg_daily_earnings": avg_daily,
        "weekly_settlement": weekly_settlement,
        "active_days_last_week": active_days,
        "source": f"{config['label']} Partner API (mock)",
        "verified": True,
    }
