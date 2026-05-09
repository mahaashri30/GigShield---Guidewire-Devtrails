"""
DSS Engine — Unified Training Script
=====================================
Trains a single XGBoost model to predict DSS (0.0–1.0) for all 5 disruption types:
  0 = heavy_rain
  1 = extreme_heat
  2 = aqi_spike
  3 = traffic_disruption
  4 = civic_emergency

Data sources:
  - Real: 7-city weather CSVs (1990–2022) → rain + heat DSS
  - Real: 26-city AQI CSV (2015–2020)     → aqi DSS
  - Synthetic: derived from rain+infra     → traffic DSS
  - Synthetic: state strike priors         → civic DSS

Generalization strategy:
  City name is NEVER a feature.
  Model learns from raw sensor values + infra_score + month.
  Works for any location in India — seen or unseen during training.

Run:
  cd gigshield/backend
  python -m ml.dss_engine.train
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
import joblib
import warnings
warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
WEATHER_DIR = os.path.join(BASE_DIR, "Temperature_And_Precipitation_Cities_IN")
AQI_PATH    = os.path.join(BASE_DIR, "AQI", "city_day.csv")
MODEL_PATH  = os.path.join(BASE_DIR, "model.joblib")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.joblib")

# ── City metadata ─────────────────────────────────────────────────────────────
# infra_score: 0.30 (excellent) → 1.0 (very poor)  — from infra_service._KNOWN_SCORES
# col_index:   cost of living multiplier             — from platform_service.CITY_ECONOMICS
# pop_density: relative population density (0–1 normalized)
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

# AQI city name → infra + col mapping
AQI_CITY_META = {
    "Ahmedabad":         {"infra": 0.50, "col": 1.05, "pop": 0.75},
    "Aizawl":            {"infra": 0.75, "col": 0.80, "pop": 0.20},
    "Amaravati":         {"infra": 0.60, "col": 0.90, "pop": 0.40},
    "Amritsar":          {"infra": 0.55, "col": 0.90, "pop": 0.60},
    "Bengaluru":         {"infra": 0.60, "col": 1.30, "pop": 0.85},
    "Bhopal":            {"infra": 0.60, "col": 0.90, "pop": 0.55},
    "Brajrajnagar":      {"infra": 0.75, "col": 0.80, "pop": 0.30},
    "Chandigarh":        {"infra": 0.40, "col": 1.10, "pop": 0.60},
    "Chennai":           {"infra": 0.50, "col": 1.20, "pop": 0.80},
    "Coimbatore":        {"infra": 0.52, "col": 1.00, "pop": 0.65},
    "Delhi":             {"infra": 0.35, "col": 1.35, "pop": 0.95},
    "Ernakulam":         {"infra": 0.48, "col": 1.05, "pop": 0.70},
    "Gurugram":          {"infra": 0.42, "col": 1.30, "pop": 0.80},
    "Guwahati":          {"infra": 0.70, "col": 0.80, "pop": 0.55},
    "Hyderabad":         {"infra": 0.45, "col": 1.15, "pop": 0.80},
    "Jaipur":            {"infra": 0.55, "col": 1.00, "pop": 0.65},
    "Jorapokhar":        {"infra": 0.75, "col": 0.80, "pop": 0.35},
    "Kochi":             {"infra": 0.48, "col": 1.05, "pop": 0.70},
    "Kolkata":           {"infra": 0.60, "col": 1.10, "pop": 0.90},
    "Lucknow":           {"infra": 0.60, "col": 0.95, "pop": 0.65},
    "Mumbai":            {"infra": 0.55, "col": 1.45, "pop": 1.00},
    "Patna":             {"infra": 0.80, "col": 0.75, "pop": 0.70},
    "Shillong":          {"infra": 0.72, "col": 0.85, "pop": 0.30},
    "Talcher":           {"infra": 0.75, "col": 0.80, "pop": 0.30},
    "Thiruvananthapuram":{"infra": 0.50, "col": 1.00, "pop": 0.60},
    "Visakhapatnam":     {"infra": 0.55, "col": 0.95, "pop": 0.65},
}

# Disruption type encoding
DTYPE_RAIN    = 0
DTYPE_HEAT    = 1
DTYPE_AQI     = 2
DTYPE_TRAFFIC = 3
DTYPE_CIVIC   = 4


# ── DSS Label Generation (Level 2 formula — ground truth) ────────────────────

def rain_dss(prcp_mm: float, infra: float) -> float:
    """
    Rain DSS = continuous function of rainfall intensity + infrastructure quality.
    Poor drainage (high infra score) amplifies the same rainfall into higher income loss.
    Calibrated against IMD thresholds: 7.6mm=moderate, 35.6mm=heavy, 64.5mm=extreme.
    """
    if prcp_mm <= 0:
        return 0.0
    # Base DSS from rainfall intensity (log-scaled for diminishing returns)
    base = np.clip(np.log1p(prcp_mm) / np.log1p(100), 0.0, 1.0)
    # Infrastructure amplifier: poor drainage = more impact
    # infra 0.30 (good) → amplifier 0.85 | infra 1.0 (poor) → amplifier 1.40
    infra_amp = 0.85 + (infra - 0.30) * (0.55 / 0.70)
    infra_amp = np.clip(infra_amp, 0.85, 1.40)
    return float(np.clip(base * infra_amp, 0.0, 1.0))


def heat_dss(tmax_c: float, infra: float, month: int) -> float:
    """
    Heat DSS = continuous function of max temperature.
    Below 40°C = no disruption. Above 46°C = full disruption.
    Summer months (Apr-Jun) amplified slightly.
    """
    if tmax_c < 38.0:
        return 0.0
    base = np.clip((tmax_c - 38.0) / 10.0, 0.0, 1.0)
    # Urban heat island: dense cities (high pop, poor infra) feel heat more
    heat_amp = 0.90 + (infra - 0.30) * (0.30 / 0.70)
    # Peak summer boost
    summer_boost = 1.10 if month in (4, 5, 6) else 1.0
    return float(np.clip(base * heat_amp * summer_boost, 0.0, 1.0))


def aqi_dss(aqi: float, infra: float) -> float:
    """
    AQI DSS = continuous function of AQI value.
    Below 100 = no disruption. Above 400 = severe disruption.
    Outdoor workers (delivery) are more exposed than office workers.
    """
    if aqi <= 100:
        return 0.0
    base = np.clip((aqi - 100) / 350.0, 0.0, 1.0)
    # Dense cities with poor infra have less green cover → worse AQI impact
    aqi_amp = 0.90 + (infra - 0.30) * (0.25 / 0.70)
    return float(np.clip(base * aqi_amp, 0.0, 1.0))


def traffic_dss(prcp_mm: float, tmax_c: float, infra: float, pop_density: float, month: int) -> float:
    """
    Traffic DSS derived from weather + infrastructure + population density.
    Rain floods roads. Heat causes breakdowns. Dense cities = worse gridlock.
    """
    rain_component = rain_dss(prcp_mm, infra) * 0.55
    heat_component = heat_dss(tmax_c, infra, month) * 0.20
    # Population density amplifier: denser city = worse traffic
    pop_amp = 0.70 + pop_density * 0.50
    base = (rain_component + heat_component) * pop_amp
    # Minimum traffic disruption in dense cities even without weather
    min_traffic = 0.05 * pop_density
    return float(np.clip(base + min_traffic, 0.0, 0.90))


def civic_dss(month: int, infra: float, pop_density: float, state_strike_prior: float) -> float:
    """
    Civic DSS (bandh/curfew/strike) — synthetic but state-aware.
    Historical strike frequency by state (Kerala, Bengal, Maharashtra highest).
    Peak months: Jan (Republic Day), Aug (Independence), Oct-Nov (festival season).
    """
    # Monthly civic risk (based on historical Indian strike/bandh patterns)
    monthly_risk = {
        1: 0.15,  # Republic Day protests
        2: 0.08,
        3: 0.10,
        4: 0.08,
        5: 0.12,  # Labour Day
        6: 0.08,
        7: 0.10,
        8: 0.18,  # Independence Day + monsoon frustration
        9: 0.10,
        10: 0.12, # Festival season disruptions
        11: 0.12,
        12: 0.10,
    }
    base = monthly_risk.get(month, 0.10)
    # State prior: Kerala=0.9, Bengal=0.85, Maharashtra=0.75, UP=0.60, others=0.40
    base *= state_strike_prior
    # Dense cities have more organized strikes
    pop_amp = 0.80 + pop_density * 0.40
    return float(np.clip(base * pop_amp, 0.0, 1.0))


# ── State strike priors (based on historical data) ───────────────────────────
STATE_STRIKE_PRIOR = {
    "Bangalore": 0.75, "Chennai": 0.70, "Delhi": 0.65, "Lucknow": 0.55,
    "Mumbai": 0.75, "Jodhpur": 0.45, "Bhubaneswar": 0.60, "Rourkela": 0.60,
    "Ahmedabad": 0.55, "Kolkata": 0.85, "Hyderabad": 0.65, "Kochi": 0.90,
    "Patna": 0.60, "Guwahati": 0.65, "Chandigarh": 0.50,
}
DEFAULT_STRIKE_PRIOR = 0.55


# ── Data Loading & Preprocessing ─────────────────────────────────────────────

def load_weather_data() -> pd.DataFrame:
    """
    Load all city weather CSVs.
    Preprocessing:
      - prcp nulls → 0.0 (no rain recorded = no rain)
      - tmax nulls → rolling 7-day mean interpolation
      - Remove extreme outliers (prcp > 500mm/day = sensor error)
      - Extract month from date
    """
    frames = []
    for city, meta in CITY_META.items():
        path = os.path.join(WEATHER_DIR, meta["file"])
        if not os.path.exists(path):
            print(f"  [WARN] Missing: {path}")
            continue
        df = pd.read_csv(path)
        df["time"] = pd.to_datetime(df["time"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["time"])
        df["city"]        = city
        df["infra"]       = meta["infra"]
        df["col_index"]   = meta["col"]
        df["pop_density"] = meta["pop"]
        df["strike_prior"]= STATE_STRIKE_PRIOR.get(city, DEFAULT_STRIKE_PRIOR)

        # Fill prcp nulls with 0 (no rain = 0mm)
        df["prcp"] = df["prcp"].fillna(0.0)

        # Interpolate tmax nulls with rolling 7-day mean
        df["tmax"] = df["tmax"].interpolate(method="linear", limit=14)
        df["tmax"] = df["tmax"].fillna(df["tmax"].median())

        # Remove sensor errors
        df = df[df["prcp"] <= 500]
        df = df[df["tmax"] <= 55]
        df = df[df["tmax"] >= 0]

        df["month"] = df["time"].dt.month
        frames.append(df[["city", "month", "prcp", "tmax", "infra", "col_index", "pop_density", "strike_prior"]])

    result = pd.concat(frames, ignore_index=True)
    print(f"  Weather rows loaded: {len(result):,}")
    return result


def load_aqi_data() -> pd.DataFrame:
    """
    Load AQI city_day CSV.
    Preprocessing:
      - Drop rows where AQI is null
      - Cap AQI at 500 (above = sensor malfunction, e.g. 2049)
      - Map city names to infra/col metadata
      - Extract month
    """
    df = pd.read_csv(AQI_PATH, parse_dates=["Date"])
    df = df.dropna(subset=["AQI"])
    df["AQI"] = df["AQI"].clip(upper=500)
    df["month"] = df["Date"].dt.month

    # Map city metadata
    df["infra"]        = df["City"].map(lambda c: AQI_CITY_META.get(c, {}).get("infra", 0.55))
    df["col_index"]    = df["City"].map(lambda c: AQI_CITY_META.get(c, {}).get("col", 1.0))
    df["pop_density"]  = df["City"].map(lambda c: AQI_CITY_META.get(c, {}).get("pop", 0.60))
    df["strike_prior"] = df["City"].map(lambda c: STATE_STRIKE_PRIOR.get(c, DEFAULT_STRIKE_PRIOR))

    # Use PM2.5 as supplementary feature (strong AQI predictor)
    df["pm25"] = df["PM2.5"].fillna(df["PM2.5"].median()).clip(upper=300)

    result = df[["City", "month", "AQI", "pm25", "infra", "col_index", "pop_density", "strike_prior"]].copy()
    result.rename(columns={"City": "city", "AQI": "aqi"}, inplace=True)
    print(f"  AQI rows loaded: {len(result):,}")
    return result


# ── Feature Engineering ───────────────────────────────────────────────────────

def build_rain_heat_rows(weather: pd.DataFrame) -> pd.DataFrame:
    """
    Build training rows for rain and heat disruption types.
    Each weather row generates up to 4 training samples:
      - rain DSS (if prcp > 0)
      - heat DSS (if tmax > 38)
      - traffic DSS (derived from rain + heat + infra + pop)
      - civic DSS (derived from month + state prior)
    """
    rows = []
    for _, r in weather.iterrows():
        month      = int(r["month"])
        prcp       = float(r["prcp"])
        tmax       = float(r["tmax"])
        infra      = float(r["infra"])
        col        = float(r["col_index"])
        pop        = float(r["pop_density"])
        strike     = float(r["strike_prior"])

        # Season encoding (cyclical)
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)

        # Rain row
        if prcp > 0:
            dss = rain_dss(prcp, infra)
            rows.append({
                "disruption_type": DTYPE_RAIN,
                "raw_value":       prcp,
                "raw_value2":      0.0,       # secondary sensor (pm25 for AQI, 0 for others)
                "infra_score":     infra,
                "col_index":       col,
                "pop_density":     pop,
                "month_sin":       month_sin,
                "month_cos":       month_cos,
                "dss":             dss,
            })

        # Heat row
        if tmax >= 38.0:
            dss = heat_dss(tmax, infra, month)
            rows.append({
                "disruption_type": DTYPE_HEAT,
                "raw_value":       tmax,
                "raw_value2":      0.0,
                "infra_score":     infra,
                "col_index":       col,
                "pop_density":     pop,
                "month_sin":       month_sin,
                "month_cos":       month_cos,
                "dss":             dss,
            })

        # Traffic row (every row — traffic exists even without extreme weather)
        dss = traffic_dss(prcp, tmax, infra, pop, month)
        rows.append({
            "disruption_type": DTYPE_TRAFFIC,
            "raw_value":       prcp,
            "raw_value2":      tmax,
            "infra_score":     infra,
            "col_index":       col,
            "pop_density":     pop,
            "month_sin":       month_sin,
            "month_cos":       month_cos,
            "dss":             dss,
        })

        # Civic row (every row — civic risk exists year-round)
        dss = civic_dss(month, infra, pop, strike)
        rows.append({
            "disruption_type": DTYPE_CIVIC,
            "raw_value":       0.0,
            "raw_value2":      0.0,
            "infra_score":     infra,
            "col_index":       col,
            "pop_density":     pop,
            "month_sin":       month_sin,
            "month_cos":       month_cos,
            "dss":             dss,
        })

    return pd.DataFrame(rows)


def build_aqi_rows(aqi: pd.DataFrame) -> pd.DataFrame:
    """Build training rows for AQI disruption type."""
    rows = []
    for _, r in aqi.iterrows():
        month     = int(r["month"])
        aqi_val   = float(r["aqi"])
        pm25      = float(r["pm25"])
        infra     = float(r["infra"])
        col       = float(r["col_index"])
        pop       = float(r["pop_density"])

        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)

        dss = aqi_dss(aqi_val, infra)
        rows.append({
            "disruption_type": DTYPE_AQI,
            "raw_value":       aqi_val,
            "raw_value2":      pm25,
            "infra_score":     infra,
            "col_index":       col,
            "pop_density":     pop,
            "month_sin":       month_sin,
            "month_cos":       month_cos,
            "dss":             dss,
        })
    return pd.DataFrame(rows)


# ── Training ──────────────────────────────────────────────────────────────────

FEATURES = [
    "disruption_type",
    "raw_value",
    "raw_value2",
    "infra_score",
    "col_index",
    "pop_density",
    "month_sin",
    "month_cos",
]


def train():
    print("\n=== DSS Engine Training ===\n")

    # 1. Load data
    print("[1/5] Loading datasets...")
    weather = load_weather_data()
    aqi     = load_aqi_data()

    # 2. Build feature rows
    print("[2/5] Engineering features...")
    rain_heat_traffic_civic = build_rain_heat_rows(weather)
    aqi_rows                = build_aqi_rows(aqi)
    df = pd.concat([rain_heat_traffic_civic, aqi_rows], ignore_index=True)
    print(f"  Total training rows: {len(df):,}")
    print(f"  DSS distribution:")
    for dtype, name in [(0,"rain"),(1,"heat"),(2,"aqi"),(3,"traffic"),(4,"civic")]:
        sub = df[df["disruption_type"] == dtype]
        print(f"    {name}: {len(sub):,} rows | dss mean={sub['dss'].mean():.3f} | max={sub['dss'].max():.3f}")

    # 3. Preprocessing
    print("[3/5] Preprocessing & normalizing...")

    # Remove DSS=0 rows for rain/heat/aqi (no disruption = not useful for learning severity)
    # Keep all traffic and civic rows (they always have some value)
    mask_keep = (
        (df["disruption_type"].isin([DTYPE_TRAFFIC, DTYPE_CIVIC])) |
        (df["dss"] > 0.0)
    )
    df = df[mask_keep].copy()
    print(f"  After removing zero-DSS rows: {len(df):,}")

    # Add small noise to DSS labels to prevent overfitting to formula
    np.random.seed(42)
    df["dss"] = (df["dss"] + np.random.normal(0, 0.01, len(df))).clip(0.0, 1.0)

    X = df[FEATURES].values
    y = df["dss"].values

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.15, random_state=42
    )

    # 4. Train XGBoost
    print("[4/5] Training XGBoost...")
    model = xgb.XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30,
        eval_metric="mae",
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # 5. Evaluate
    print("[5/5] Evaluating...")
    preds = model.predict(X_test)
    preds = np.clip(preds, 0.0, 1.0)
    mae   = mean_absolute_error(y_test, preds)
    r2    = r2_score(y_test, preds)
    print(f"\n  Overall MAE : {mae:.4f}")
    print(f"  Overall R²  : {r2:.4f}")

    # Per disruption type evaluation
    df_test_idx = df.iloc[len(X_train):]
    print("\n  Per disruption type (test set):")
    for dtype, name in [(0,"rain"),(1,"heat"),(2,"aqi"),(3,"traffic"),(4,"civic")]:
        mask = df["disruption_type"].values[len(X_train):] == dtype
        if mask.sum() == 0:
            continue
        type_mae = mean_absolute_error(y_test[mask], preds[mask])
        print(f"    {name:10}: MAE={type_mae:.4f} | n={mask.sum():,}")

    # Feature importance
    print("\n  Feature importances:")
    for feat, imp in sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1]):
        print(f"    {feat:20}: {imp:.4f}")

    # Save
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"\n  Model  → {MODEL_PATH}")
    print(f"  Scaler → {SCALER_PATH}")
    print("\n=== Training complete ===\n")
    return model, scaler


if __name__ == "__main__":
    train()
