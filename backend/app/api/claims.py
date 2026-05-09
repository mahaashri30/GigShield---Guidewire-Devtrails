from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.models import Worker, Policy, Claim, DisruptionEvent, Payout, PolicyStatus, ClaimStatus, PayoutStatus, DisruptionType
from app.schemas.schemas import ClaimResponse
from app.services.auth_service import get_current_worker, get_current_auth_context, AuthContext
from app.services.premium_service import calculate_payout, MAX_DAILY_PAYOUT, MAX_WEEKLY_PAYOUT, get_dynamic_caps
from app.services.fraud_service import calculate_fraud_score
from app.services.infra_service import get_infra_adjusted_dss
from app.services.payout_service import initiate_upi_payout
from app.services.notification_service import notify_claim_approved, notify_claim_rejected, notify_claim_paid

router = APIRouter()

CITY_POOLS = {
    "Delhi":          [DisruptionType.AQI_SPIKE, DisruptionType.EXTREME_HEAT, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Mumbai":         [DisruptionType.HEAVY_RAIN, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Bangalore":      [DisruptionType.HEAVY_RAIN, DisruptionType.AQI_SPIKE, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Chennai":        [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Hyderabad":      [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Coimbatore":     [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Tiruchirappalli": [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Tiruchchirappalli": [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Madurai":        [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Salem":          [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
    "Pune":           [DisruptionType.HEAVY_RAIN, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Kolkata":        [DisruptionType.HEAVY_RAIN, DisruptionType.AQI_SPIKE, DisruptionType.CIVIC_EMERGENCY],
    "Ahmedabad":      [DisruptionType.EXTREME_HEAT, DisruptionType.AQI_SPIKE, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Lucknow":        [DisruptionType.EXTREME_HEAT, DisruptionType.AQI_SPIKE, DisruptionType.TRAFFIC_DISRUPTION, DisruptionType.CIVIC_EMERGENCY],
    "Patna":          [DisruptionType.HEAVY_RAIN, DisruptionType.EXTREME_HEAT, DisruptionType.CIVIC_EMERGENCY],
}

MIN_DISRUPTION_HOURS = {
    "heavy_rain":         0.5,
    "extreme_heat":       2.0,
    "aqi_spike":          1.0,
    "traffic_disruption": 0.5,
    "civic_emergency":    1.0,
}
ACTIVE_HOUR_START = 6
ACTIVE_HOUR_END = 22
TOTAL_ACTIVE_HOURS = 16.0


def is_within_active_hours(dt: datetime) -> bool:
    ist_hour = (dt.hour + 5) % 24
    return ACTIVE_HOUR_START <= ist_hour < ACTIVE_HOUR_END


def active_hours_ratio(event: object) -> float:
    started = event.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    ended = event.ended_at
    if ended is None:
        ended = datetime.now(timezone.utc)
    if ended.tzinfo is None:
        ended = ended.replace(tzinfo=timezone.utc)

    ist_offset = timedelta(hours=5, minutes=30)
    start_ist = started + ist_offset
    end_ist   = ended   + ist_offset

    day_start = start_ist.replace(hour=ACTIVE_HOUR_START, minute=0, second=0, microsecond=0)
    day_end   = start_ist.replace(hour=ACTIVE_HOUR_END,   minute=0, second=0, microsecond=0)

    effective_start = max(start_ist, day_start)
    effective_end   = min(end_ist,   day_end)

    if effective_start >= day_end:
        return 0.0

    actual_hours = max(0.0, (effective_end - effective_start).total_seconds() / 3600)
    return round(actual_hours / TOTAL_ACTIVE_HOURS, 3)


import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/trigger/{disruption_event_id}", response_model=ClaimResponse)
async def trigger_claim(
    disruption_event_id: str,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth_context),
):
    current_worker = auth.worker
    now = datetime.now(timezone.utc)

    # ── Active policy ─────────────────────────────────────────────────────────
    result = await db.execute(
        select(Policy).where(
            Policy.worker_id == current_worker.id,
            Policy.status == PolicyStatus.ACTIVE,
        ).order_by(Policy.created_at.desc()).with_for_update()
    )
    policy = None
    for p in result.scalars().all():
        end = p.end_date.replace(tzinfo=timezone.utc) if p.end_date.tzinfo is None else p.end_date
        if end >= now:
            policy = p
            break
    if not policy:
        raise HTTPException(status_code=400, detail="No active policy found")

    end_date = policy.end_date
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    if end_date < now:
        policy.status = PolicyStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Policy has expired")

    # ── Disruption event ──────────────────────────────────────────────────────
    result = await db.execute(select(DisruptionEvent).where(DisruptionEvent.id == disruption_event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Disruption event not found")

    if event.city.lower() != current_worker.city.lower():
        raise HTTPException(status_code=400, detail="Disruption event is not in your city")

    allowed_types = CITY_POOLS.get(current_worker.city, list(DisruptionType))
    if event.disruption_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"{event.disruption_type} is not covered in {current_worker.city} pool")

    event_started_at = event.started_at
    if event_started_at.tzinfo is None:
        event_started_at = event_started_at.replace(tzinfo=timezone.utc)

    # ── Hours ratio + minimum duration check ─────────────────────────────────
    hours_ratio = active_hours_ratio(event)

    if not auth.is_dev_mode:
        min_hours = MIN_DISRUPTION_HOURS.get(event.disruption_type.value, 0.5)
        min_ratio = round(min_hours / TOTAL_ACTIVE_HOURS, 3)
        if hours_ratio < min_ratio:
            elapsed_minutes = round((now - event_started_at).total_seconds() / 60, 1)
            required_minutes = int(min_hours * 60)
            raise HTTPException(
                status_code=400,
                detail=f"Disruption must persist for at least {required_minutes} min before claiming. "
                       f"Current duration: {elapsed_minutes} min."
            )
    if auth.is_dev_mode and hours_ratio <= 0.0:
        hours_ratio = 0.1

    # ── Proximity factor ──────────────────────────────────────────────────────
    from app.models.models import WorkerLocationPing
    worker_prefix = current_worker.pincode[:3] if current_worker.pincode else ""
    event_prefix = (event.pincode or "")[:3]
    proximity_factor = 1.0

    last_ping_result = await db.execute(
        select(WorkerLocationPing).where(
            WorkerLocationPing.worker_id == current_worker.id,
        ).order_by(WorkerLocationPing.recorded_at.desc()).limit(1)
    )
    last_ping = last_ping_result.scalar_one_or_none()

    if last_ping and event.lat and event.lng:
        distance = haversine(last_ping.lat, last_ping.lng, event.lat, event.lng)
        radius = event.radius_km or 5.0
        if distance <= radius:
            proximity_factor = 1.0
        elif distance <= radius * 2:
            proximity_factor = 0.7
        else:
            proximity_factor = 0.4
    elif event_prefix and worker_prefix and worker_prefix != event_prefix:
        proximity_factor = 0.7

    # ── Duplicate claim check ─────────────────────────────────────────────────
    dup = await db.execute(
        select(Claim).where(
            Claim.worker_id == current_worker.id,
            Claim.disruption_event_id == disruption_event_id,
        )
    )
    existing_claim = dup.scalar_one_or_none()
    if existing_claim:
        if not auth.is_dev_mode:
            raise HTTPException(status_code=400, detail="Already claimed this disruption event")
        # Dev mode: delete old claim so simulate can re-trigger cleanly
        await db.delete(existing_claim)
        await db.commit()

    # ── Claims history for fraud ──────────────────────────────────────────────
    week_ago = now - timedelta(days=7)
    claims_this_week = (await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == current_worker.id,
            Claim.created_at >= week_ago,
        )
    )).scalar() or 0

    twelve_weeks_ago = now - timedelta(weeks=12)
    hist_count = (await db.execute(
        select(func.count(Claim.id)).where(
            Claim.worker_id == current_worker.id,
            Claim.created_at >= twelve_weeks_ago,
        )
    )).scalar() or 0
    worker_avg_claims_per_week = round(hist_count / 12.0, 2) if hist_count > 0 else 0.0

    zone_prefix = current_worker.pincode[:3] if current_worker.pincode else ""
    zone_claim_count = (await db.execute(
        select(func.count(Claim.id)).where(
            Claim.disruption_event_id == disruption_event_id,
        ).join(Worker).where(Worker.pincode.like(f"{zone_prefix}%"))
    )).scalar() or 0

    zone_total_workers = (await db.execute(
        select(func.count(Worker.id)).where(
            Worker.pincode.like(f"{zone_prefix}%"),
            Worker.is_active == True,
        )
    )).scalar() or 0

    ping_cutoff = now - timedelta(minutes=30)
    had_suspicious_ping = (await db.execute(
        select(WorkerLocationPing).where(
            WorkerLocationPing.worker_id == current_worker.id,
            WorkerLocationPing.is_suspicious == True,
            WorkerLocationPing.recorded_at >= ping_cutoff,
        ).limit(1)
    )).scalar_one_or_none() is not None

    last_known_city = last_ping.city_detected if last_ping else ""
    had_device_off_gap = bool(last_ping and last_ping.gap_minutes and last_ping.gap_minutes > 90)
    sim_changed = current_worker.sim_changed_at is not None and current_worker.sim_changed_at > event_started_at

    fraud_result = calculate_fraud_score(
        worker_city=current_worker.city,
        event_city=event.city,
        worker_pincode=current_worker.pincode,
        event_pincode=event.pincode or "",
        was_platform_active=True,
        claims_this_week=claims_this_week,
        claims_same_event=0,
        event_started_at=event_started_at,
        claim_created_at=now,
        disruption_type=event.disruption_type,
        last_known_city=last_known_city,
        had_suspicious_ping=had_suspicious_ping,
        active_hours_ratio=hours_ratio,
        claim_amount_ratio=1.0,
        worker_avg_claims_per_week=worker_avg_claims_per_week,
        zone_avg_claims_per_event=0.0,
        zone_claim_count_this_event=zone_claim_count,
        zone_total_workers=zone_total_workers,
        sim_changed=sim_changed,
        had_device_off_gap=had_device_off_gap,
    )

    # Dev mode: bypass fraud checks — always auto-approve for demo
    if auth.is_dev_mode:
        fraud_result["auto_approve"] = True
        fraud_result["auto_reject"] = False
        fraud_result["fraud_score"] = 0.0
        fraud_result["flags"] = []
        fraud_result["flags_json"] = "[]"

    # ── Caps ──────────────────────────────────────────────────────────────────
    daily_cap, weekly_cap_dynamic = get_dynamic_caps(policy.tier, current_worker.city)
    weekly_cap = weekly_cap_dynamic
    weekly_claimed = float(policy.total_claimed or 0)
    weekly_remaining = max(0.0, weekly_cap - weekly_claimed)

    if weekly_remaining <= 0:
        raise HTTPException(status_code=400, detail="Weekly payout cap reached for this policy")

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    claimed_today = float((await db.execute(
        select(func.coalesce(func.sum(Claim.approved_amount), 0.0)).where(
            Claim.worker_id == current_worker.id,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]),
            Claim.created_at >= today_start,
        )
    )).scalar() or 0)

    daily_remaining = max(0.0, daily_cap - claimed_today)
    effective_cap = min(daily_remaining, weekly_remaining)

    # ── Infra-adjusted DSS + hours ratio ─────────────────────────────────────
    from app.services.infra_service import get_activity_zone_infra_score
    activity_infra = await get_activity_zone_infra_score(
        worker_id=current_worker.id,
        db=db,
        fallback_city=current_worker.city,
        fallback_pincode=current_worker.pincode,
        days=30,
    )

    adjusted_dss, infra_hours_ratio, infra_score = await get_infra_adjusted_dss(
        base_dss=event.dss_multiplier,
        city=current_worker.city,
        pincode=current_worker.pincode,
        disruption_type=event.disruption_type.value,
        severity=event.severity.value,
        activity_zone_infra=activity_infra,
    )

    # Dev mode: use infra_hours_ratio directly (realistic demo payout)
    # Real mode: min of actual elapsed vs infra-based duration (conservative)
    if auth.is_dev_mode:
        effective_hours_ratio = round(infra_hours_ratio * proximity_factor, 3)
    else:
        effective_hours_ratio = round(
            min(hours_ratio, infra_hours_ratio) * proximity_factor, 3
        )

    # ── Platform baseline + income loss (Phase 1: GPS proxy + order drop model)
    # Phase 2: replace with Blinkit/Zepto/Swiggy partner API
    from app.services.platform_service import get_worker_baseline, compute_income_loss, DEFAULT_ONLINE_HOURS_PER_DAY, DEFAULT_ORDERS_PER_DAY

    baseline = await get_worker_baseline(
        worker_id=current_worker.id,
        db=db,
        avg_daily_earnings=current_worker.avg_daily_earnings,
        avg_online_hours=current_worker.avg_online_hours_per_day or DEFAULT_ONLINE_HOURS_PER_DAY,
        avg_orders_per_day=current_worker.avg_orders_per_day or DEFAULT_ORDERS_PER_DAY,
    )

    # disruption_hours: how long the disruption actually ran
    # Dev mode: use infra_hours_ratio * 16h (realistic for demo)
    # Real mode: actual elapsed time since event started
    if auth.is_dev_mode:
        disruption_hours = infra_hours_ratio * TOTAL_ACTIVE_HOURS
    else:
        disruption_hours = max(0.1, (now - event_started_at).total_seconds() / 3600)

    income_loss_data = compute_income_loss(
        baseline=baseline,
        disruption_type=event.disruption_type.value,
        severity=event.severity.value,
        disruption_hours=disruption_hours,
    )
    income_loss_ratio = income_loss_data["income_loss_ratio"]

    print(f"[Claims] platform={current_worker.platform} "
          f"online={baseline['avg_online_hours_per_day']}h/day "
          f"orders={baseline['avg_orders_per_day']}/day "
          f"hourly=Rs.{baseline['avg_hourly_earnings']} "
          f"drop={income_loss_ratio*100:.0f}% "
          f"loss=Rs.{income_loss_data['income_loss']} "
          f"source={baseline['data_source']}")

    # ── Final payout calculation ──────────────────────────────────────────────
    # payout = daily_avg x dss x effective_hours x income_loss_ratio
    payout_data = calculate_payout(
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=adjusted_dss,
        active_hours_ratio=round(effective_hours_ratio * income_loss_ratio, 3),
        tier=policy.tier,
        existing_claimed_today=claimed_today,
    )

    claim = Claim(
        worker_id=current_worker.id,
        policy_id=policy.id,
        disruption_event_id=event.id,
        status=ClaimStatus.PENDING,
        claimed_amount=payout_data["raw_payout"],
        worker_daily_avg=current_worker.avg_daily_earnings,
        dss_multiplier=adjusted_dss,
        active_hours_ratio=effective_hours_ratio,
        fraud_score=fraud_result["fraud_score"],
        fraud_flags=fraud_result["flags_json"],
        auto_approved=fraud_result["auto_approve"],
    )

    if fraud_result["auto_approve"]:
        approved = min(payout_data["approved_amount"], effective_cap)
        claim.status = ClaimStatus.APPROVED
        claim.approved_amount = round(approved, 2)
        claim.processed_at = now
        policy.total_claimed = round(weekly_claimed + approved, 2)
        policy.claims_count = (policy.claims_count or 0) + 1
    elif fraud_result["auto_reject"]:
        claim.status = ClaimStatus.REJECTED
        claim.rejection_reason = "; ".join(fraud_result["flags"])
        claim.processed_at = now

    db.add(claim)
    await db.commit()
    await db.refresh(claim)

    if claim.status == ClaimStatus.REJECTED:
        await notify_claim_rejected(db, current_worker, claim)
        await db.commit()

    if claim.status == ClaimStatus.APPROVED and (claim.approved_amount or 0) > 0:
        await notify_claim_approved(db, current_worker, claim, event.disruption_type.value)
        upi_id = current_worker.upi_id or "worker_" + current_worker.id[:8] + "@upi"
        payout_result = await initiate_upi_payout(
            worker_id=current_worker.id,
            upi_id=upi_id,
            amount=claim.approved_amount,
            claim_id=claim.id,
            phone=current_worker.phone,
            disruption_type=event.disruption_type.value,
            bank_account=current_worker.bank_account or "",
            bank_ifsc=current_worker.bank_ifsc or "",
            trigger_time=event_started_at,
        )
        channel = payout_result.get("channel", "UPI")
        settlement_secs = payout_result.get("settlement_seconds", 0)
        payout = Payout(
            claim_id=claim.id,
            worker_id=current_worker.id,
            amount=claim.approved_amount,
            upi_id=upi_id,
            status=PayoutStatus.COMPLETED if payout_result["success"] else (
                PayoutStatus.ROLLED_BACK if payout_result.get("rollback") else PayoutStatus.FAILED
            ),
            razorpay_payout_id=payout_result.get("payout_id"),
            transaction_ref=payout_result.get("transaction_ref"),
            completed_at=now if payout_result["success"] else None,
            channel=channel,
            settlement_seconds=settlement_secs,
            reconciled=payout_result["success"],
        )
        if payout_result["success"]:
            claim.status = ClaimStatus.PAID
            await notify_claim_paid(db, current_worker, claim, upi_id, payout_result.get("transaction_ref", ""))
        elif payout_result.get("rollback"):
            policy.total_claimed = round(max(0.0, float(policy.total_claimed or 0) - (claim.approved_amount or 0)), 2)
            policy.claims_count = max(0, (policy.claims_count or 1) - 1)
        db.add(payout)
        await db.commit()
        await db.refresh(claim)

    return claim


@router.get("/", response_model=list[ClaimResponse])
async def list_claims(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    result = await db.execute(
        select(Claim)
        .where(Claim.worker_id == current_worker.id)
        .order_by(Claim.created_at.desc())
    )
    return result.scalars().all()
