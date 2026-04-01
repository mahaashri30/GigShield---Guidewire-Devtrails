"""
Fraud Detection — Isolation Forest Training Script
Run: python -m ml.fraud_detection.train

Trains an unsupervised anomaly detection model on synthetic claim data.
Covers all 5 disruption types including civic emergencies (curfews, strikes, zone closures).
Phase 2: Retrain weekly with real claim + GPS + platform + civic data.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.joblib")

# Disruption type encoding
# 0=heavy_rain, 1=extreme_heat, 2=aqi_spike, 3=traffic_disruption, 4=civic_emergency


def generate_claims_data(n_clean=4500, n_fraud=500):
    """Generate synthetic claim data covering all 5 disruption types"""
    np.random.seed(42)

    # Clean claims — genuine workers across all disruption types
    clean = pd.DataFrame({
        "city_match": np.ones(n_clean),
        "platform_active": np.random.binomial(1, 0.95, n_clean),
        "claims_this_week": np.random.poisson(1.2, n_clean).clip(0, 5),
        "time_delta_seconds": np.random.exponential(300, n_clean).clip(30, 3600),
        "active_hours_ratio": np.random.uniform(0.5, 1.0, n_clean),
        "claim_amount_ratio": np.random.uniform(0.3, 1.0, n_clean),
        # Disruption type distribution for genuine claims
        "disruption_type": np.random.choice([0, 1, 2, 3, 4], n_clean,
                                             p=[0.30, 0.20, 0.20, 0.15, 0.15]),
        # Civic emergency: genuine workers have verifiable location history
        "location_consistent": np.random.binomial(1, 0.97, n_clean),
        "label": np.zeros(n_clean),
    })

    # Fraudulent claims — GPS spoof, inactive, high frequency, instant claims
    # Civic emergency fraud: fake curfew/strike claims from unaffected zones
    fraud = pd.DataFrame({
        "city_match": np.random.binomial(1, 0.2, n_fraud),
        "platform_active": np.random.binomial(1, 0.3, n_fraud),
        "claims_this_week": np.random.poisson(5.0, n_fraud).clip(3, 15),
        "time_delta_seconds": np.random.uniform(0, 10, n_fraud),
        "active_hours_ratio": np.random.uniform(0.0, 0.3, n_fraud),
        "claim_amount_ratio": np.ones(n_fraud),
        # Fraud rings disproportionately exploit civic emergencies
        # (harder to verify than weather — no objective sensor data)
        "disruption_type": np.random.choice([0, 1, 2, 3, 4], n_fraud,
                                             p=[0.15, 0.10, 0.10, 0.20, 0.45]),
        # Fraudsters have no consistent location history
        "location_consistent": np.random.binomial(1, 0.1, n_fraud),
        "label": np.ones(n_fraud),
    })

    return pd.concat([clean, fraud], ignore_index=True).sample(frac=1, random_state=42)


def train():
    print("Generating synthetic claims data (all 5 disruption types)...")
    df = generate_claims_data()

    features = [
        "city_match", "platform_active", "claims_this_week",
        "time_delta_seconds", "active_hours_ratio", "claim_amount_ratio",
        "disruption_type", "location_consistent",
    ]
    X = df[features]

    print("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Training Isolation Forest...")
    model = IsolationForest(
        n_estimators=200,
        contamination=0.1,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    preds = model.predict(X_scaled)
    n_flagged = (preds == -1).sum()
    print(f"Flagged {n_flagged}/{len(df)} samples as anomalies ({n_flagged/len(df)*100:.1f}%)")

    # Civic emergency fraud detection rate
    civic_mask = df["disruption_type"] == 4
    civic_fraud = df[civic_mask & (df["label"] == 1)]
    civic_preds = model.predict(scaler.transform(civic_fraud[features]))
    civic_caught = (civic_preds == -1).sum()
    print(f"Civic emergency fraud caught: {civic_caught}/{len(civic_fraud)} ({civic_caught/max(len(civic_fraud),1)*100:.1f}%)")

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Scaler saved to {SCALER_PATH}")


if __name__ == "__main__":
    train()
