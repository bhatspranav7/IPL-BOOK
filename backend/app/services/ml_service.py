import joblib
import numpy as np
from datetime import datetime

model = joblib.load("app/ml/demand_model.pkl")

def predict_demand(seats_remaining, time_to_match):
    now = datetime.now()

    hour = now.hour
    day_of_week = now.weekday()

    features = np.array([[hour, day_of_week, seats_remaining, time_to_match]])

    prediction = model.predict(features)[0]

    return float(prediction)