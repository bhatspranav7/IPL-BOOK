import logging
from datetime import datetime

import joblib
import pandas as pd

from app.ml.train_model import MODEL_PATH, train

logger = logging.getLogger(__name__)


def _load():
    try:
        bundle = joblib.load(MODEL_PATH)
        if isinstance(bundle, dict) and bundle.get("version") == 2:
            return bundle
        logger.warning("Outdated demand model format - retraining")
    except Exception as e:
        logger.warning("Could not load demand model (%s) - retraining", e)
    return train(verbose=False)


_bundle = _load()
model = _bundle["model"]
FEATURES = _bundle["features"]
MODEL_MAE = _bundle.get("mae")


def predict_demand(occupancy: float, hours_to_match: float, now: datetime | None = None):
    now = now or datetime.now()

    features = pd.DataFrame(
        [[now.hour, now.weekday(), occupancy, hours_to_match]],
        columns=FEATURES
    )

    prediction = model.predict(features)[0]

    return float(min(max(prediction, 0.0), 1.0))
