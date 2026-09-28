"""Train the demand model.

The feature set is scale-free (occupancy instead of absolute seat counts) so the
same model works for a 50-seat demo match and a 40,000-seat stadium.

Run from backend/:  python -m app.ml.train_model
"""
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

FEATURES = ["hour", "day_of_week", "occupancy", "hours_to_match"]
MODEL_PATH = os.path.join(os.path.dirname(__file__), "demand_model.pkl")
REAL_DATA_PATH = os.path.join(os.path.dirname(__file__), "booking_data.csv")


def synthetic_dataset(n: int = 6000, seed: int = 7) -> pd.DataFrame:
    """Booking demand curves: scarcity and urgency dominate, evenings and weekends add a bump."""
    rng = np.random.default_rng(seed)

    hour = rng.integers(0, 24, n)
    day_of_week = rng.integers(0, 7, n)
    occupancy = rng.beta(2, 2, n)
    hours_to_match = rng.exponential(96, n).clip(0, 24 * 30)

    scarcity = occupancy ** 1.6
    urgency = np.exp(-hours_to_match / 48)
    evening = np.where((hour >= 18) & (hour <= 23), 0.08, 0.0)
    weekend = np.where(day_of_week >= 5, 0.06, 0.0)

    demand = 0.55 * scarcity + 0.35 * urgency + evening + weekend
    demand = (demand + rng.normal(0, 0.03, n)).clip(0, 1)

    return pd.DataFrame({
        "hour": hour,
        "day_of_week": day_of_week,
        "occupancy": occupancy,
        "hours_to_match": hours_to_match,
        "demand_score": demand,
    })


def train(verbose: bool = True):
    df = synthetic_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        df[FEATURES], df["demand_score"], test_size=0.2, random_state=7
    )

    model = GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=7)
    model.fit(X_train, y_train)

    mae = mean_absolute_error(y_test, model.predict(X_test))
    bundle = {"model": model, "features": FEATURES, "mae": round(float(mae), 4), "version": 2}

    joblib.dump(bundle, MODEL_PATH)
    if verbose:
        print(f"✅ Demand model trained on {len(df)} rows - test MAE {mae:.4f}")
    return bundle


if __name__ == "__main__":
    train()
