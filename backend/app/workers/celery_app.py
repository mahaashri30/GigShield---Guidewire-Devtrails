"""
Celery background workers for GigShield
Handles periodic disruption monitoring and auto-claim triggering
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "gigshield",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.beat_schedule = {
    # Poll weather + all 5 disruption triggers every 15 minutes
    "poll-weather": {
        "task": "app.workers.tasks.poll_weather_all_cities",
        "schedule": 900.0,  # 15 min
    },
    # Poll AQI every 60 minutes (dedicated pass)
    "poll-aqi": {
        "task": "app.workers.tasks.poll_aqi_all_cities",
        "schedule": 3600.0,
    },
    # Expire old policies daily
    "expire-policies": {
        "task": "app.workers.tasks.expire_old_policies",
        "schedule": 86400.0,
    },
}

celery_app.conf.timezone = "Asia/Kolkata"
