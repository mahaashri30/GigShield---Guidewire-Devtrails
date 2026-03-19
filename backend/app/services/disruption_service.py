"""
Disruption Monitoring Service
Polls weather, AQI, and traffic APIs.
Uses mock data for Phase 1 prototype.
"""
import httpx
import random
from datetime import datetime
from typing import Optional
from app.config import settings
from app.models.models import DisruptionType, DisruptionSeverity

# DSS multiplier lookup
DSS_TABLE = {
    DisruptionType.HEAVY_RAIN: {
        DisruptionSeverity.MODERATE: 0.3,
        DisruptionSeverity.SEVERE: 0.6,
        DisruptionSeverity.EXTREME: 1.0,
    },
    DisruptionType.EXTREME_HEAT: {
        DisruptionSeverity.MODERATE: 0.3,
        DisruptionSeverity.SEVERE: 0.6,
        DisruptionSeverity.EXTREME: 1.0,
    },
    DisruptionType.AQI_SPIKE: {
        DisruptionSeverity.MODERATE: 0.2,
        DisruptionSeverity.SEVERE: 0.5,
        DisruptionSeverity.EXTREME: 1.0,
    },
    DisruptionType.TRAFFIC_DISRUPTION: {
        DisruptionSeverity.MODERATE: 0.3,
        DisruptionSeverity.SEVERE: 0.5,
        DisruptionSeverity.EXTREME: 0.8,
    },
    DisruptionType.CIVIC_EMERGENCY: {
        DisruptionSeverity.MODERATE: 0.5,
        DisruptionSeverity.SEVERE: 0.8,
        DisruptionSeverity.EXTREME: 1.0,
    },
}


def get_dss(disruption_type: DisruptionType, severity: DisruptionSeverity) -> float:
    return DSS_TABLE.get(disruption_type, {}).get(severity, 0.3)


async def fetch_weather_mock(city: str) -> dict:
    """Mock weather data for Phase 1 prototype"""
    mock_scenarios = {
        "Mumbai": {
            "rainfall_mm_per_hr": random.choice([0, 0, 0, 45.0, 75.0, 120.0]),
            "temperature_c": random.uniform(28, 34),
            "description": "Moderate rain",
        },
        "Delhi": {
            "rainfall_mm_per_hr": random.choice([0, 0, 0, 0, 15.0]),
            "temperature_c": random.choice([38.0, 42.0, 44.0, 46.5]),
            "description": "Clear sky, extreme heat",
        },
        "Bangalore": {
            "rainfall_mm_per_hr": random.choice([0, 0, 55.0, 80.0]),
            "temperature_c": random.uniform(24, 32),
            "description": "Heavy rain",
        },
        "Chennai": {
            "rainfall_mm_per_hr": random.choice([0, 0, 30.0, 90.0]),
            "temperature_c": random.uniform(30, 36),
            "description": "Thunderstorm",
        },
    }
    return mock_scenarios.get(city, {
        "rainfall_mm_per_hr": 0,
        "temperature_c": 32.0,
        "description": "Clear",
    })


async def fetch_aqi_mock(city: str) -> dict:
    """Mock AQI data for Phase 1 prototype"""
    aqi_map = {
        "Delhi": random.choice([180, 280, 360, 420]),
        "Mumbai": random.choice([80, 120, 160]),
        "Bangalore": random.choice([60, 90, 110]),
        "Chennai": random.choice([70, 100, 130]),
    }
    aqi = aqi_map.get(city, 80)
    return {"aqi": aqi, "city": city}


async def fetch_weather_real(city: str) -> dict:
    """Real OpenWeather API call"""
    if settings.OPENWEATHER_API_KEY == "mock_key":
        return await fetch_weather_mock(city)
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city + ",IN", "appid": settings.OPENWEATHER_API_KEY, "units": "metric"},
                timeout=5.0,
            )
            data = r.json()
            rain = data.get("rain", {}).get("1h", 0.0) * 60  # convert to per-hour
            return {
                "rainfall_mm_per_hr": rain,
                "temperature_c": data["main"]["temp"],
                "description": data["weather"][0]["description"],
            }
        except Exception:
            return await fetch_weather_mock(city)


def classify_rain(mm_per_hr: float) -> Optional[tuple]:
    """Returns (severity, description) or None if no trigger"""
    if mm_per_hr >= 115 / 24:  # ~4.8mm/hr sustained → 115mm/day
        return DisruptionSeverity.EXTREME, f"{mm_per_hr:.1f}mm/hr rainfall (Extreme)"
    elif mm_per_hr >= 64.5:
        return DisruptionSeverity.SEVERE, f"{mm_per_hr:.1f}mm/hr rainfall (Heavy)"
    elif mm_per_hr >= 35:
        return DisruptionSeverity.MODERATE, f"{mm_per_hr:.1f}mm/hr rainfall (Moderate)"
    return None


def classify_heat(temp_c: float) -> Optional[tuple]:
    if temp_c >= 46:
        return DisruptionSeverity.EXTREME, f"{temp_c:.1f}°C (Extreme heat)"
    elif temp_c >= 44:
        return DisruptionSeverity.SEVERE, f"{temp_c:.1f}°C (Severe heat)"
    elif temp_c >= 42:
        return DisruptionSeverity.MODERATE, f"{temp_c:.1f}°C (Heatwave)"
    return None


def classify_aqi(aqi: int) -> Optional[tuple]:
    if aqi > 400:
        return DisruptionSeverity.EXTREME, f"AQI {aqi} (Severe)"
    elif aqi > 300:
        return DisruptionSeverity.SEVERE, f"AQI {aqi} (Very Poor)"
    elif aqi > 200:
        return DisruptionSeverity.MODERATE, f"AQI {aqi} (Poor)"
    return None


async def check_disruptions(city: str, pincode: str) -> list:
    """Check all disruption triggers for a city and return active events"""
    events = []

    weather = await fetch_weather_real(city)
    aqi_data = await fetch_aqi_mock(city)

    # Rain check
    rain_result = classify_rain(weather.get("rainfall_mm_per_hr", 0))
    if rain_result:
        severity, desc = rain_result
        events.append({
            "disruption_type": DisruptionType.HEAVY_RAIN,
            "severity": severity,
            "city": city,
            "pincode": pincode,
            "dss_multiplier": get_dss(DisruptionType.HEAVY_RAIN, severity),
            "raw_value": weather["rainfall_mm_per_hr"],
            "description": desc,
            "source": "OpenWeather API",
        })

    # Heat check
    heat_result = classify_heat(weather.get("temperature_c", 30))
    if heat_result:
        severity, desc = heat_result
        events.append({
            "disruption_type": DisruptionType.EXTREME_HEAT,
            "severity": severity,
            "city": city,
            "pincode": pincode,
            "dss_multiplier": get_dss(DisruptionType.EXTREME_HEAT, severity),
            "raw_value": weather["temperature_c"],
            "description": desc,
            "source": "OpenWeather API",
        })

    # AQI check
    aqi_result = classify_aqi(aqi_data.get("aqi", 0))
    if aqi_result:
        severity, desc = aqi_result
        events.append({
            "disruption_type": DisruptionType.AQI_SPIKE,
            "severity": severity,
            "city": city,
            "pincode": pincode,
            "dss_multiplier": get_dss(DisruptionType.AQI_SPIKE, severity),
            "raw_value": aqi_data["aqi"],
            "description": desc,
            "source": "AQI India API",
        })

    return events
