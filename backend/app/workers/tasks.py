"""
Celery tasks — Phase 1 stubs, fully implemented in Phase 2
"""
import asyncio
from app.workers.celery_app import celery_app

SUPPORTED_CITIES = [
    ("Bangalore", "560001"),
    ("Mumbai", "400001"),
    ("Delhi", "110001"),
    ("Chennai", "600001"),
    ("Hyderabad", "500001"),
]


@celery_app.task(name="app.workers.tasks.poll_weather_all_cities")
def poll_weather_all_cities():
    """
    Polls OpenWeather API for all supported cities.
    On threshold breach → creates DisruptionEvent → triggers auto-claims.
    Full implementation: Phase 2
    """
    print("[Celery] Polling weather for all cities...")
    for city, pincode in SUPPORTED_CITIES:
        print(f"  Checking {city}...")
    return {"status": "polled", "cities": len(SUPPORTED_CITIES)}


@celery_app.task(name="app.workers.tasks.poll_aqi_all_cities")
def poll_aqi_all_cities():
    """Polls AQI API for all cities. Full implementation: Phase 2"""
    print("[Celery] Polling AQI for all cities...")
    return {"status": "polled"}


@celery_app.task(name="app.workers.tasks.expire_old_policies")
def expire_old_policies():
    """Marks expired policies. Full implementation: Phase 2"""
    print("[Celery] Expiring old policies...")
    return {"status": "done"}


@celery_app.task(name="app.workers.tasks.process_auto_claims")
def process_auto_claims(disruption_event_id: str, city: str):
    """
    Auto-triggers claims for all active policy holders in affected city.
    Called after a disruption event is created.
    Full implementation: Phase 2
    """
    print(f"[Celery] Auto-claiming for event {disruption_event_id} in {city}")
    return {"status": "triggered", "event_id": disruption_event_id}
