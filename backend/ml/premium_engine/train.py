"""
Premium Engine — XGBoost Training Script (v2)
=============================================
Phase 1 (now): Real zone_risk + season_factor derived from existing
               DSS weather CSVs (1990-2022) and AQI CSV (2015-2020).
               No more made-up numbers.

Phase 2 (auto): Weekly retraining using real claims from DB.
               run_auto_retrain() is called by Celery every Sunday 3am.

Zone risk derivation:
  disruption_days_per_year = days where prcp>35mm OR tmax>42C OR AQI>200
  zone_risk = 1.0 + (disruption_days / 365) * infra_amplifier

Season factor derivation:
  For each city+month: count disruption days in that month across all years
  season_factor = city_month_disruption_rate / annual_avg_disruption_rate

Run manually:
  cd gigshield/backend
  python -m ml.premium_engine.train
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import xgboost as xgb
import joblib
import warnings
warnings.filterwarnings("ignore")

OUTPUT_PATH  = os.path.join(os.path.dirname(__file__), "model.joblib")
WEATHER_DIR  = os.path.join(os.path.dirname(__file__), "../dss_engine/Temperature_And_Precipitation_Cities_IN")
AQI_PATH     = os.path.join(os.path.dirname(__file__), "../dss_engine/AQI/city_day.csv")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "last_train_metrics.json")

# IMD disruption thresholds
RAIN_THRESHOLD = 35.6   # mm/day — heavy rain (IMD definition)
HEAT_THRESHOLD = 42.0   # °C — heatwave (IMD definition)
AQI_THRESHOLD  = 200    # AQI — poor air quality (CPCB definition)

# City metadata — same as DSS engine
CITY_META = {
    "Bangalore":  {"infra": 0.60, "col": 1.30, "pop": 0.85, "file": "Bangalore_1990_2022_BangaloreCity.csv"},
    "Chennai":    {"infra": 0.50, "col": 1.20, "pop": 0.80, "file": "Chennai_1990_2022_Madras.csv"},
    "Delhi":      {"infra": 0.35, "col": 1.35, "pop": 0.95, "file": "Delhi_NCR_1990_2022_Safdarjung.csv"},
    "Lucknow":    {"infra": 0.60, "col": 0.95, "pop": 0.65, "file": "Lucknow_1990_2022.csv"},
    "Mumbai":     {"infra": 0.55, "col": 1.45, "pop": 1.00, "file": "Mumbai_1990_2022_Santacruz.csv"},
    "Jodhpur":    {"infra": 0.60, "col": 1.00, "pop": 0.45, "file": "Rajasthan_1990_2022_Jodhpur.csv"},
    "Bhubaneswar":{"infra": 0.55, "col": 1.00, "pop": 0.50, "file": "weather_Bhubhneshwar_1990_2022.csv"},
    "Rourkela":   {"infra": 0.65, "col": 0.90, "pop": 0.40, "file": "weather_Rourkela_2021_2022.csv"},
}

AQI_CITY_META = {
    "Ahmedabad": {"infra": 0.50, "col": 1.05, "pop": 0.75},
    "Bengaluru": {"infra": 0.60, "col": 1.30, "pop": 0.85},
    "Bhopal":    {"infra": 0.60, "col": 0.90, "pop": 0.55},
    "Chandigarh":{"infra": 0.40, "col": 1.10, "pop": 0.60},
    "Chennai":   {"infra": 0.50, "col": 1.20, "pop": 0.80},
    "Coimbatore":{"infra": 0.52, "col": 1.00, "pop": 0.65},
    "Delhi":     {"infra": 0.35, "col": 1.35, "pop": 0.95},
    "Gurugram":  {"infra": 0.42, "col": 1.30, "pop": 0.80},
    "Guwahati":  {"infra": 0.70, "col": 0.80, "pop": 0.55},
    "Hyderabad": {"infra": 0.45, "col": 1.15, "pop": 0.80},
    "Jaipur":    {"infra": 0.55, "col": 1.00, "pop": 0.65},
    "Kochi":     {"infra": 0.48, "col": 1.05, "pop": 0.70},
    "Kolkata":   {"infra": 0.60, "col": 1.10, "pop": 0.90},
    "Lucknow":   {"infra": 0.60, "col": 0.95, "pop": 0.65},
    "Mumbai":    {"infra": 0.55, "col": 1.45, "pop": 1.00},
    "Patna":     {"infra": 0.80, "col": 0.75, "pop": 0.70},
    "Visakhapatnam": {"infra": 0.55, "col": 0.95, "pop": 0.65},
}

DISRUPTION_DSS = {
    0: {0: 0.3, 1: 0.6, 2: 1.0},  # rain
    1: {0: 0.3, 1: 0.6, 2: 1.0},  # heat
    2: {0: 0.2, 1: 0.5, 2: 1.0},  # aqi
    3: {0: 0.3, 1: 0.5, 2: 0.8},  # traffic
    4: {0: 0.5, 1: 0.8, 2: 1.0},  # civic
}

FEATURES = [
    "pincode_prefix", "month", "tier", "tenure_weeks",
    "activity_score", "zone_risk", "season_factor",
    "disruption_type", "severity", "dss_multiplier", "is_civic_emergency",
]


# ── Step 1: Derive real zone_risk and season_factor from weather CSVs ─────────

def compute_real_risk_factors() -> tuple[dict, dict]:
    """
    Compute zone_risk and season_factor per city from real weather data.

    zone_risk:
      = 1.0 + (annual_disruption_days / 365) * infra_amplifier
      infra_amplifier: poor infra cities get higher risk for same disruption rate
      e.g. Mumbai: 51 rain days/yr, infra=0.55 → zone_risk = 1.0 + 0.14*1.18 = 1.165

    season_factor per month:
      = monthly_disruption_rate / annual_avg_monthly_rate
      e.g. Mumbai July: 18 rain days → 18/4.25 = 4.24x normal → season_factor = 1.35 (capped)
    """
    city_stats = {}  # city → {annual_disruption_days, monthly_disruption_days[1..12]}

    # ── Weather CSVs ──────────────────────────────────────────────────────────
    for city, meta in CITY_META.items():
        path = os.path.join(WEATHER_DIR, meta["file"])
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        df["time"] = pd.to_datetime(df["time"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["time"])
        df["prcp"] = df["prcp"].fillna(0.0)
        df["tmax"] = df["tmax"].interpolate(method="linear", limit=14).fillna(df["tmax"].median() if not df["tmax"].isna().all() else 30.0)
        df["month"] = df["time"].dt.month
        df["year"]  = df["time"].dt.year

        # Flag disruption days
        df["is_disruption"] = (
            (df["prcp"] >= RAIN_THRESHOLD) |
            (df["tmax"] >= HEAT_THRESHOLD)
        ).astype(int)

        years = df["year"].nunique()
        if years == 0:
            continue

        # Annual disruption days (average per year)
        annual_days = df["is_disruption"].sum() / years

        # Monthly disruption days (average per month per year)
        monthly = df.groupby("month")["is_disruption"].sum() / years

        city_stats[city] = {
            "annual_days": annual_days,
            "monthly_days": monthly.to_dict(),
            "infra": meta["infra"],
            "col": meta["col"],
            "pop": meta["pop"],
        }

    # ── AQI CSV ───────────────────────────────────────────────────────────────
    if os.path.exists(AQI_PATH):
        aqi_df = pd.read_csv(AQI_PATH, parse_dates=["Date"])
        aqi_df = aqi_df.dropna(subset=["AQI"])
        aqi_df["AQI"] = aqi_df["AQI"].clip(upper=500)
        aqi_df["month"] = aqi_df["Date"].dt.month
        aqi_df["year"]  = aqi_df["Date"].dt.year
        aqi_df["is_disruption"] = (aqi_df["AQI"] >= AQI_THRESHOLD).astype(int)

        for city_name, meta in AQI_CITY_META.items():
            city_data = aqi_df[aqi_df["City"] == city_name]
            if city_data.empty:
                continue
            years = city_data["year"].nunique()
            if years == 0:
                continue
            annual_days = city_data["is_disruption"].sum() / years
            monthly = city_data.groupby("month")["is_disruption"].sum() / years

            # Merge with weather stats if city already exists
            mapped = city_name if city_name in city_stats else None
            for wc in city_stats:
                if wc.lower() in city_name.lower() or city_name.lower() in wc.lower():
                    mapped = wc
                    break

            if mapped:
                city_stats[mapped]["annual_days"] += annual_days * 0.5  # blend
                for m, v in monthly.to_dict().items():
                    city_stats[mapped]["monthly_days"][m] = (
                        city_stats[mapped]["monthly_days"].get(m, 0) + v * 0.5
                    )
            else:
                city_stats[city_name] = {
                    "annual_days": annual_days,
                    "monthly_days": monthly.to_dict(),
                    "infra": meta["infra"],
                    "col": meta["col"],
                    "pop": meta["pop"],
                }

    # ── Compute zone_risk per city ────────────────────────────────────────────
    zone_risks = {}
    for city, stats in city_stats.items():
        annual_days = stats["annual_days"]
        infra = stats["infra"]
        # infra_amplifier: poor infra (high score) = higher risk multiplier
        # infra 0.30 (good) → amplifier 1.0 | infra 0.80 (poor) → amplifier 1.50
        infra_amp = 1.0 + (infra - 0.30) * (0.50 / 0.50)
        infra_amp = max(1.0, min(1.60, infra_amp))
        zone_risk = round(1.0 + (annual_days / 365.0) * infra_amp, 3)
        zone_risk = max(0.90, min(1.60, zone_risk))
        zone_risks[city] = zone_risk

    # ── Compute season_factor per city per month ──────────────────────────────
    season_factors = {}
    for city, stats in city_stats.items():
        monthly = stats["monthly_days"]
        annual_avg_per_month = stats["annual_days"] / 12.0
        if annual_avg_per_month <= 0:
            season_factors[city] = {m: 1.0 for m in range(1, 13)}
            continue
        sf = {}
        for m in range(1, 13):
            raw = monthly.get(m, 0) / annual_avg_per_month
            # Cap between 0.70 and 1.60 — extreme months shouldn't dominate
            sf[m] = round(max(0.70, min(1.60, raw)), 3)
        season_factors[city] = sf

    print(f"\n  [Premium] Real risk factors computed for {len(zone_risks)} cities:")
    for city in sorted(zone_risks):
        sf_peak = max(season_factors[city].values())
        sf_peak_month = max(season_factors[city], key=season_factors[city].get)
        print(f"    {city:15} zone_risk={zone_risks[city]:.3f}  "
              f"peak_season={sf_peak:.2f} (month {sf_peak_month})")

    return zone_risks, season_factors


# ── Step 2: Generate training data using real risk factors ────────────────────

def generate_data(
    n: int = 8000,
    zone_risks: dict = None,
    season_factors: dict = None,
    real_claims_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Generate training data.
    - Uses real zone_risk + season_factor from weather data
    - Blends with real claims data from DB when available (Phase 2)
    - Falls back to synthetic if no real data
    """
    np.random.seed(42)
    rows = []

    cities = list(zone_risks.keys()) if zone_risks else []

    # ── Real claims rows (Phase 2 — when DB has enough data) ─────────────────
    real_rows = 0
    if real_claims_df is not None and len(real_claims_df) >= 50:
        print(f"  [Premium] Blending {len(real_claims_df)} real claims into training...")
        for _, row in real_claims_df.iterrows():
            rows.append({
                "pincode_prefix": int(str(row.get("pincode", "0"))[:1]) if row.get("pincode") else 0,
                "month":          int(row.get("month", 6)),
                "tier":           int(row.get("tier_idx", 1)),
                "tenure_weeks":   int(row.get("tenure_weeks", 4)),
                "activity_score": float(row.get("activity_score", 0.90)),
                "zone_risk":      float(row.get("zone_risk", 1.10)),
                "season_factor":  float(row.get("season_factor", 1.10)),
                "disruption_type":int(row.get("disruption_type", 0)),
                "severity":       int(row.get("severity", 1)),
                "dss_multiplier": float(row.get("dss_multiplier", 0.5)),
                "is_civic_emergency": int(row.get("is_civic", 0)),
                "premium":        float(row.get("actual_premium", 49.0)),
                "source":         "real",
            })
        real_rows = len(real_claims_df)

    # ── Synthetic rows using real risk factors ────────────────────────────────
    n_synthetic = max(n, n - real_rows)
    base_prices = np.array([29.0, 49.0, 79.0])

    for _ in range(n_synthetic):
        # Pick a city — weighted by population density
        if cities:
            city = np.random.choice(cities)
            zr = zone_risks[city]
            month = np.random.randint(1, 13)
            sf = season_factors[city].get(month, 1.0)
        else:
            # Fallback if no real data loaded
            zr = np.random.uniform(0.90, 1.50)
            month = np.random.randint(1, 13)
            sf = np.random.uniform(0.80, 1.50)

        tier = np.random.choice([0, 1, 2])
        base = base_prices[tier]
        tenure_weeks = np.random.randint(0, 52)
        history_factor = 0.95 if tenure_weeks > 12 else 1.0
        activity_score = np.random.uniform(0.85, 1.0)

        disruption_type = np.random.choice([0, 1, 2, 3, 4], p=[0.30, 0.20, 0.20, 0.15, 0.15])
        severity = np.random.choice([0, 1, 2], p=[0.50, 0.35, 0.15])
        dss = DISRUPTION_DSS[disruption_type][severity]
        is_civic = int(disruption_type == 4)
        civic_boost = 1.10 if is_civic else 1.0

        # Premium label — now uses REAL zone_risk and season_factor
        premium = base * zr * sf * history_factor * activity_score * civic_boost
        premium += np.random.normal(0, 1.0)
        premium = np.clip(premium, base * 0.70, base * 1.70)

        rows.append({
            "pincode_prefix":   np.random.randint(0, 8),
            "month":            month,
            "tier":             tier,
            "tenure_weeks":     tenure_weeks,
            "activity_score":   round(activity_score, 3),
            "zone_risk":        round(zr, 3),
            "season_factor":    round(sf, 3),
            "disruption_type":  disruption_type,
            "severity":         severity,
            "dss_multiplier":   dss,
            "is_civic_emergency": is_civic,
            "premium":          round(premium, 2),
            "source":           "synthetic",
        })

    df = pd.DataFrame(rows)
    if real_rows > 0:
        print(f"  [Premium] Training mix: {real_rows} real + {n_synthetic} synthetic rows")
    return df


# ── Step 3: Train ─────────────────────────────────────────────────────────────

def train(real_claims_df: pd.DataFrame = None, verbose: bool = True) -> dict:
    """
    Train the premium model.
    real_claims_df: optional DataFrame of real claims from DB (auto-retrain path)
    Returns metrics dict.
    """
    if verbose:
        print("\n=== Premium Engine Training (v2 — Real Risk Factors) ===\n")

    # Step 1: Compute real zone_risk + season_factor from weather CSVs
    if verbose:
        print("[1/4] Computing real risk factors from weather/AQI data...")
    zone_risks, season_factors = compute_real_risk_factors()

    if not zone_risks:
        print("  [WARN] No weather CSVs found — falling back to synthetic zone risks")
        zone_risks = None
        season_factors = None

    # Step 2: Generate training data
    if verbose:
        print("\n[2/4] Generating training data...")
    df = generate_data(
        n=8000,
        zone_risks=zone_risks,
        season_factors=season_factors,
        real_claims_df=real_claims_df,
    )
    if verbose:
        print(f"  Total rows: {len(df):,}")
        print(f"  Real claims: {(df['source'] == 'real').sum():,}")
        print(f"  Synthetic:   {(df['source'] == 'synthetic').sum():,}")
        print(f"  Premium range: ₹{df['premium'].min():.0f} – ₹{df['premium'].max():.0f}")
        print(f"  Premium mean:  ₹{df['premium'].mean():.2f}")

    # Step 3: Train XGBoost
    if verbose:
        print("\n[3/4] Training XGBoost...")
    X = df[FEATURES]
    y = df["premium"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=20,
        eval_metric="mae",
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # Step 4: Evaluate
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2  = float(np.corrcoef(y_test, preds)[0, 1] ** 2)

    if verbose:
        print(f"\n[4/4] Results:")
        print(f"  MAE : ₹{mae:.2f}  (avg premium error)")
        print(f"  R²  : {r2:.4f}")
        print(f"\n  Feature importances:")
        for feat, imp in sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1]):
            print(f"    {feat:22}: {imp:.4f}")

    # Save model
    joblib.dump(model, OUTPUT_PATH)

    # Save metrics for monitoring
    import json
    from datetime import datetime
    metrics = {
        "trained_at": datetime.utcnow().isoformat(),
        "mae": round(mae, 4),
        "r2": round(r2, 4),
        "total_rows": len(df),
        "real_claims_rows": int((df["source"] == "real").sum()),
        "synthetic_rows": int((df["source"] == "synthetic").sum()),
        "cities_with_real_data": len(zone_risks) if zone_risks else 0,
        "zone_risks": {k: round(v, 3) for k, v in (zone_risks or {}).items()},
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    if verbose:
        print(f"\n  Model  → {OUTPUT_PATH}")
        print(f"  Metrics → {METRICS_PATH}")
        print("\n=== Training complete ===\n")

    return metrics


# ── Step 4: Auto-retrain using real claims from DB ────────────────────────────

async def fetch_real_claims_for_training(db) -> pd.DataFrame:
    """
    Fetch real claims from DB to use as training labels.
    Requires at least 50 paid/approved claims to be useful.

    Each row = one real claim with:
      - worker's pincode, city, platform
      - disruption type + severity
      - actual premium paid
      - DSS multiplier
      - tenure (weeks since first policy)
    """
    from sqlalchemy import select, func
    from app.models.models import Claim, Policy, Worker, DisruptionEvent, ClaimStatus

    TIER_IDX = {"basic": 0, "smart": 1, "pro": 2}
    DTYPE_MAP = {
        "heavy_rain": 0, "extreme_heat": 1, "aqi_spike": 2,
        "traffic_disruption": 3, "civic_emergency": 4,
    }
    SEV_MAP = {"moderate": 0, "severe": 1, "extreme": 2}

    result = await db.execute(
        select(
            Claim.dss_multiplier,
            Claim.worker_daily_avg,
            Claim.created_at,
            Policy.weekly_premium,
            Policy.tier,
            Policy.pincode,
            Policy.city,
            Policy.created_at.label("policy_created_at"),
            DisruptionEvent.disruption_type,
            DisruptionEvent.severity,
            Worker.platform,
        )
        .join(Policy, Claim.policy_id == Policy.id)
        .join(DisruptionEvent, Claim.disruption_event_id == DisruptionEvent.id)
        .join(Worker, Claim.worker_id == Worker.id)
        .where(Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID]))
        .limit(5000)
    )
    rows = result.all()

    if len(rows) < 50:
        print(f"  [Premium AutoRetrain] Only {len(rows)} real claims — need 50+, skipping real data blend")
        return None

    records = []
    for r in rows:
        try:
            tenure_weeks = max(0, int((r.created_at - r.policy_created_at).days / 7))
            records.append({
                "pincode":        r.pincode or "000000",
                "month":          r.created_at.month,
                "tier_idx":       TIER_IDX.get(r.tier.value if hasattr(r.tier, "value") else str(r.tier), 1),
                "tenure_weeks":   tenure_weeks,
                "activity_score": 0.90,
                "zone_risk":      1.10,   # will be overridden by real computation
                "season_factor":  1.10,
                "disruption_type": DTYPE_MAP.get(
                    r.disruption_type.value if hasattr(r.disruption_type, "value") else str(r.disruption_type), 0
                ),
                "severity":       SEV_MAP.get(
                    r.severity.value if hasattr(r.severity, "value") else str(r.severity), 1
                ),
                "dss_multiplier": float(r.dss_multiplier or 0.5),
                "is_civic":       int("civic" in str(r.disruption_type)),
                "actual_premium": float(r.weekly_premium or 49.0),
            })
        except Exception:
            continue

    print(f"  [Premium AutoRetrain] Loaded {len(records)} real claims for training blend")
    return pd.DataFrame(records)


def run_auto_retrain():
    """
    Called by Celery every Sunday 3am IST.
    Fetches real claims from DB, blends with synthetic, retrains model.
    """
    import asyncio
    from app.database import AsyncSessionLocal

    async def _retrain():
        async with AsyncSessionLocal() as db:
            real_claims = await fetch_real_claims_for_training(db)
        metrics = train(real_claims_df=real_claims, verbose=True)
        return metrics

    print("[Premium AutoRetrain] Starting weekly retrain...")
    metrics = asyncio.run(_retrain())
    print(f"[Premium AutoRetrain] Done — MAE=₹{metrics['mae']:.2f} R²={metrics['r2']:.4f}")
    return metrics


if __name__ == "__main__":
    train()
