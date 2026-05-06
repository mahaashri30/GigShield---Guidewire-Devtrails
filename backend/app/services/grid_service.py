"""
Worker Delivery Grid Service
============================
Builds a personal delivery grid for each worker from their GPS pings.
The grid represents the actual area the worker delivers in — not just
their registered city or pincode.

How it works:
  Every GPS ping (non-suspicious) → update_worker_grid() is called
  Grid is rebuilt from last 30 days of clean pings:
    - Bounding box: min/max lat/lng of all pings
    - Centroid: mean lat/lng (worker's "home base")
    - Radius: P90 distance from centroid (ignores outlier pings)
    - Dominant city/pincode: most frequent in pings

Used for:
  1. Claims proximity check — is disruption inside worker's delivery grid?
  2. Premium zone_risk — worker's actual delivery zone, not city average
  3. Fraud detection — claim from outside usual delivery area is suspicious

Grid builds gradually:
  Day 1   : 6 pings  → rough centroid, large radius (uncertain)
  Week 1  : 100 pings → good bounding box, reliable centroid
  Month 1 : 400 pings → stable grid, P90 radius accurate
"""
import math
from datetime import datetime, timezone, timedelta
from typing import Optional


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def update_worker_grid(
    worker_id: str,
    db,
    days: int = 30,
) -> Optional[dict]:
    """
    Rebuild the worker's delivery grid from last N days of clean GPS pings.
    Called on every non-suspicious ping.

    Returns the updated grid stats or None if not enough pings.
    Minimum 5 pings needed to build a meaningful grid.
    """
    from sqlalchemy import select, func, cast, Date
    from app.models.models import WorkerLocationPing, WorkerDeliveryGrid

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    # Fetch all clean pings in last N days
    result = await db.execute(
        select(
            WorkerLocationPing.lat,
            WorkerLocationPing.lng,
            WorkerLocationPing.city_detected,
            WorkerLocationPing.pincode_detected,
            WorkerLocationPing.recorded_at,
        ).where(
            WorkerLocationPing.worker_id == worker_id,
            WorkerLocationPing.recorded_at >= since,
            WorkerLocationPing.is_suspicious == False,
            WorkerLocationPing.lat.isnot(None),
            WorkerLocationPing.lng.isnot(None),
        ).order_by(WorkerLocationPing.recorded_at.asc())
    )
    pings = result.all()

    if len(pings) < 5:
        return None  # Not enough data yet

    lats = [p.lat for p in pings]
    lngs = [p.lng for p in pings]

    # ── Bounding box ──────────────────────────────────────────────────────────
    bbox_lat_min = min(lats)
    bbox_lat_max = max(lats)
    bbox_lng_min = min(lngs)
    bbox_lng_max = max(lngs)

    # ── Centroid ──────────────────────────────────────────────────────────────
    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)

    # ── Distances from centroid ───────────────────────────────────────────────
    distances = sorted([
        _haversine_km(center_lat, center_lng, p.lat, p.lng)
        for p in pings
    ])

    # Max radius (furthest ping)
    radius_km = round(distances[-1], 3)

    # P90 radius — 90% of pings fall within this distance
    # More robust than max (ignores outlier pings from rare long-distance trips)
    p90_idx = int(len(distances) * 0.90)
    p90_radius_km = round(distances[min(p90_idx, len(distances) - 1)], 3)

    # Minimum radius of 0.5km (GPS accuracy noise)
    p90_radius_km = max(0.5, p90_radius_km)
    radius_km = max(0.5, radius_km)

    # ── Active days ───────────────────────────────────────────────────────────
    active_days_result = await db.execute(
        select(func.count(func.distinct(cast(
            WorkerLocationPing.recorded_at, Date
        )))).where(
            WorkerLocationPing.worker_id == worker_id,
            WorkerLocationPing.recorded_at >= since,
            WorkerLocationPing.is_suspicious == False,
        )
    )
    active_days = active_days_result.scalar() or 0

    # ── Dominant city + pincode (most frequent) ───────────────────────────────
    city_counts: dict[str, int] = {}
    pincode_counts: dict[str, int] = {}
    for p in pings:
        if p.city_detected:
            city_counts[p.city_detected] = city_counts.get(p.city_detected, 0) + 1
        if p.pincode_detected:
            pincode_counts[p.pincode_detected] = pincode_counts.get(p.pincode_detected, 0) + 1

    dominant_city    = max(city_counts, key=city_counts.get) if city_counts else None
    dominant_pincode = max(pincode_counts, key=pincode_counts.get) if pincode_counts else None

    # ── Upsert grid ───────────────────────────────────────────────────────────
    existing = await db.execute(
        select(WorkerDeliveryGrid).where(WorkerDeliveryGrid.worker_id == worker_id)
    )
    grid = existing.scalar_one_or_none()

    if grid is None:
        grid = WorkerDeliveryGrid(
            worker_id=worker_id,
            first_ping_at=pings[0].recorded_at,
        )
        db.add(grid)

    grid.bbox_lat_min    = round(bbox_lat_min, 6)
    grid.bbox_lat_max    = round(bbox_lat_max, 6)
    grid.bbox_lng_min    = round(bbox_lng_min, 6)
    grid.bbox_lng_max    = round(bbox_lng_max, 6)
    grid.center_lat      = round(center_lat, 6)
    grid.center_lng      = round(center_lng, 6)
    grid.radius_km       = radius_km
    grid.p90_radius_km   = p90_radius_km
    grid.ping_count      = len(pings)
    grid.active_days     = active_days
    grid.dominant_city   = dominant_city
    grid.dominant_pincode = dominant_pincode
    grid.last_ping_at    = pings[-1].recorded_at

    await db.flush()

    return {
        "center_lat":      grid.center_lat,
        "center_lng":      grid.center_lng,
        "radius_km":       grid.radius_km,
        "p90_radius_km":   grid.p90_radius_km,
        "bbox":            [bbox_lat_min, bbox_lat_max, bbox_lng_min, bbox_lng_max],
        "ping_count":      grid.ping_count,
        "active_days":     grid.active_days,
        "dominant_city":   grid.dominant_city,
        "dominant_pincode": grid.dominant_pincode,
    }


def is_point_in_grid(
    lat: float,
    lng: float,
    grid,
    use_p90: bool = True,
) -> tuple[bool, float]:
    """
    Check if a lat/lng point (e.g. disruption epicentre) is inside
    the worker's delivery grid.

    Returns (is_inside, distance_from_center_km).

    use_p90=True  → uses P90 radius (recommended — ignores outlier pings)
    use_p90=False → uses max radius (more lenient)
    """
    if grid is None or grid.center_lat is None:
        return True, 0.0  # No grid yet — allow claim (benefit of doubt)

    distance = _haversine_km(grid.center_lat, grid.center_lng, lat, lng)
    radius = grid.p90_radius_km if use_p90 else grid.radius_km

    # Also check bounding box as a fast pre-filter
    in_bbox = (
        grid.bbox_lat_min <= lat <= grid.bbox_lat_max and
        grid.bbox_lng_min <= lng <= grid.bbox_lng_max
    )

    # Inside if within radius OR within bounding box
    # (bounding box catches edge cases where worker regularly goes to corners)
    is_inside = distance <= radius or in_bbox

    return is_inside, round(distance, 3)


async def get_worker_grid(worker_id: str, db) -> Optional[object]:
    """Fetch the worker's current delivery grid from DB."""
    from sqlalchemy import select
    from app.models.models import WorkerDeliveryGrid

    result = await db.execute(
        select(WorkerDeliveryGrid).where(WorkerDeliveryGrid.worker_id == worker_id)
    )
    return result.scalar_one_or_none()


def grid_confidence(grid) -> str:
    """
    Returns confidence level of the grid based on ping count.
    Used to decide how strictly to apply grid-based checks.
    """
    if grid is None or grid.ping_count < 5:
        return "none"       # No grid — skip grid checks
    elif grid.ping_count < 20:
        return "low"        # 1-3 days of data — use loosely
    elif grid.ping_count < 60:
        return "medium"     # 1 week of data — use with tolerance
    else:
        return "high"       # 2+ weeks of data — use strictly
