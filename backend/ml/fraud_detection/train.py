"""
Fraud Detection — Isolation Forest Training Script
Run: python -m ml.fraud_detection.train

Trains an unsupervised anomaly detection model on synthetic claim data.
Phase 1: Rule-based scoring is primary. This model is an enhancement.
Phase 2: Retrain weekly with real claim + GPS + platform data.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.joblib")


def generate_claims_data(n_clean=4500, n_fraud=500):
    """Generate synthetic claim data with embedded fraud patterns"""
    np.random.seed(42)

    # Clean claims
    clean = pd.DataFrame({
        "city_match": np.ones(n_clean),
        "platform_active": np.random.binomial(1, 0.95, n_clean),
        "claims_this_week": np.random.poisson(1.2, n_clean).clip(0, 5),
        "time_delta_seconds": np.random.exponential(300, n_clean).clip(30, 3600),
        "active_hours_ratio": np.random.uniform(0.5, 1.0, n_clean),
        "claim_amount_ratio": np.random.uniform(0.3, 1.0, n_clean),
        "label": np.zeros(n_clean),
    })

    # Fraudulent claims: GPS spoof, inactive, high frequency, instant claims
    fraud = pd.DataFrame({
        "city_match": np.random.binomial(1, 0.2, n_fraud),        # city mismatch
        "platform_active": np.random.binomial(1, 0.3, n_fraud),   # mostly offline
        "claims_this_week": np.random.poisson(5.0, n_fraud).clip(3, 15),  # high freq
        "time_delta_seconds": np.random.uniform(0, 10, n_fraud),  # suspiciously fast
        "active_hours_ratio": np.random.uniform(0.0, 0.3, n_fraud),
        "claim_amount_ratio": np.ones(n_fraud),                    # always max claim
        "label": np.ones(n_fraud),
    })

    return pd.concat([clean, fraud], ignore_index=True).sample(frac=1, random_state=42)


def train():
    print("Generating synthetic claims data...")
    df = generate_claims_data()

    features = ["city_match", "platform_active", "claims_this_week",
                "time_delta_seconds", "active_hours_ratio", "claim_amount_ratio"]
    X = df[features]

    print("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Training Isolation Forest...")
    model = IsolationForest(
        n_estimators=200,
        contamination=0.1,  # expect ~10% anomalies
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Evaluate: -1 = anomaly (fraud), 1 = normal
    preds = model.predict(X_scaled)
    n_flagged = (preds == -1).sum()
    print(f"Flagged {n_flagged}/{len(df)} samples as anomalies ({n_flagged/len(df)*100:.1f}%)")

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Scaler saved to {SCALER_PATH}")


if __name__ == "__main__":
    train()
