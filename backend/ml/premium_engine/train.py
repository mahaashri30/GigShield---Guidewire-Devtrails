"""
Premium Engine — XGBoost Model Training Script
Run: python -m ml.premium_engine.train

Generates synthetic training data and trains the dynamic premium model.
Includes all 5 disruption types: rain, heat, AQI, traffic, civic emergency.
In Phase 2, retrained weekly with real claims + weather + civic data.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import xgboost as xgb
import joblib
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

# Disruption type encoding
# 0=heavy_rain, 1=extreme_heat, 2=aqi_spike, 3=traffic_disruption, 4=civic_emergency
DISRUPTION_DSS = {
    0: {0: 0.3, 1: 0.6, 2: 1.0},  # rain
    1: {0: 0.3, 1: 0.6, 2: 1.0},  # heat
    2: {0: 0.2, 1: 0.5, 2: 1.0},  # aqi
    3: {0: 0.3, 1: 0.5, 2: 0.8},  # traffic
    4: {0: 0.5, 1: 0.8, 2: 1.0},  # civic emergency (curfew/strike/zone closure)
}


def generate_data(n=5000):
    np.random.seed(42)

    # Zone risk by pincode prefix
    zone_risks = {0: 1.0, 1: 1.2, 2: 1.35, 3: 1.15, 4: 1.1, 5: 1.05, 6: 1.0, 7: 1.05}
    pincode_prefix = np.random.randint(0, 8, n)
    zone_risk = np.array([zone_risks[p] for p in pincode_prefix])

    month = np.random.randint(1, 13, n)
    season_map = {1:1.0,2:1.0,3:1.05,4:1.1,5:1.2,6:1.3,7:1.35,8:1.3,9:1.2,10:1.05,11:1.0,12:1.0}
    season = np.array([season_map[m] for m in month])

    tier = np.random.choice([0, 1, 2], n)  # 0=basic, 1=smart, 2=pro
    base_prices = np.array([29.0, 49.0, 79.0])
    base = base_prices[tier]

    tenure_weeks = np.random.randint(0, 52, n)
    history_factor = np.where(tenure_weeks > 12, 0.95, 1.0)

    activity_score = np.random.uniform(0.85, 1.0, n)

    # Disruption type (0-4) and severity (0=moderate,1=severe,2=extreme)
    # civic_emergency (4) and traffic (3) now included in training
    disruption_type = np.random.choice([0, 1, 2, 3, 4], n,
                                        p=[0.30, 0.20, 0.20, 0.15, 0.15])
    severity = np.random.choice([0, 1, 2], n, p=[0.5, 0.35, 0.15])
    dss = np.array([DISRUPTION_DSS[dt][s] for dt, s in zip(disruption_type, severity)])

    # Civic emergency flag — 1 if curfew/strike/zone closure, 0 otherwise
    is_civic = (disruption_type == 4).astype(int)

    # Premium label
    # Civic emergencies carry higher base risk (unpredictable, full income loss)
    civic_risk_boost = np.where(is_civic == 1, 1.1, 1.0)
    premium = base * zone_risk * season * history_factor * activity_score * civic_risk_boost
    premium += np.random.normal(0, 1.5, n)
    premium = np.clip(premium, base * 0.8, base * 1.6)

    df = pd.DataFrame({
        "pincode_prefix": pincode_prefix,
        "month": month,
        "tier": tier,
        "tenure_weeks": tenure_weeks,
        "activity_score": activity_score,
        "zone_risk": zone_risk,
        "season_factor": season,
        "disruption_type": disruption_type,
        "severity": severity,
        "dss_multiplier": dss,
        "is_civic_emergency": is_civic,
        "premium": premium,
    })
    return df


def train():
    print("Generating synthetic training data (all 5 disruption types)...")
    df = generate_data(5000)

    features = [
        "pincode_prefix", "month", "tier", "tenure_weeks",
        "activity_score", "zone_risk", "season_factor",
        "disruption_type", "severity", "dss_multiplier", "is_civic_emergency",
    ]
    X = df[features]
    y = df["premium"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training XGBoost model...")
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"MAE: \u20b9{mae:.2f}")

    joblib.dump(model, OUTPUT_PATH)
    print(f"Model saved to {OUTPUT_PATH}")
    return model


if __name__ == "__main__":
    train()
