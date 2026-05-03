import asyncio
import sys
sys.path.insert(0, '.')

from app.models.models import DisruptionType as D, DisruptionSeverity as S
from app.services.dss_service import calculate_dss

TESTS = [
    ("rain   Mumbai   75mm  Jul", D.HEAVY_RAIN,         S.SEVERE,   "Mumbai",    "400001", 75.0,  None, 7),
    ("rain   Bangalore75mm  Jul", D.HEAVY_RAIN,         S.SEVERE,   "Bangalore", "560034", 75.0,  None, 7),
    ("rain   Ranchi   75mm  Jul", D.HEAVY_RAIN,         S.SEVERE,   "Ranchi",    "834001", 75.0,  None, 7),
    ("rain   Kochi    30mm  Jun", D.HEAVY_RAIN,         S.MODERATE, "Kochi",     "682001", 30.0,  None, 6),
    ("heat   Delhi    44.5C May", D.EXTREME_HEAT,       S.SEVERE,   "Delhi",     "110001", 44.5,  None, 5),
    ("heat   Jodhpur  47C   May", D.EXTREME_HEAT,       S.EXTREME,  "Jodhpur",   "342001", 47.0,  None, 5),
    ("heat   Lucknow  43C   May", D.EXTREME_HEAT,       S.MODERATE, "Lucknow",   "226001", 43.0,  None, 5),
    ("aqi    Delhi    320   Nov", D.AQI_SPIKE,          S.SEVERE,   "Delhi",     "110001", 320.0, 85.0, 11),
    ("aqi    Patna    280   Nov", D.AQI_SPIKE,          S.SEVERE,   "Patna",     "800001", 280.0, 70.0, 11),
    ("aqi    Mumbai   210   Dec", D.AQI_SPIKE,          S.MODERATE, "Mumbai",    "400001", 210.0, 55.0, 12),
    ("traffic Bangalore 72  Jul", D.TRAFFIC_DISRUPTION, S.MODERATE, "Bangalore", "560034", 72.0,  30.0, 7),
    ("traffic Delhi     80  Jan", D.TRAFFIC_DISRUPTION, S.SEVERE,   "Delhi",     "110001", 80.0,  40.0, 1),
    ("civic  Kochi    -     Aug", D.CIVIC_EMERGENCY,    S.MODERATE, "Kochi",     "682001", None,  None, 8),
    ("civic  Kolkata  -     Aug", D.CIVIC_EMERGENCY,    S.SEVERE,   "Kolkata",   "700001", None,  None, 8),
    ("civic  Varanasi -     Jan", D.CIVIC_EMERGENCY,    S.MODERATE, "Varanasi",  "221001", None,  None, 1),
]

async def main():
    print(f"\n{'Test':<35} {'DSS':>6}  {'Method':<10} {'Infra'}")
    print("-" * 65)
    for label, dtype, sev, city, pin, rv, rv2, month in TESTS:
        r = await calculate_dss(dtype, sev, city, pin, raw_value=rv, raw_value2=rv2, month=month)
        print(f"{label:<35} {r['dss']:>6.3f}  {r['method']:<10} {r['infra_score']:.2f}")
    print()

asyncio.run(main())
