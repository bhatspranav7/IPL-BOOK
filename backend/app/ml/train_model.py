import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

data = {
    "hour": [10, 12, 15, 18, 20],
    "day_of_week": [1, 2, 3, 5, 6],
    "seats_remaining": [200, 150, 100, 50, 20],
    "time_to_match": [10, 8, 6, 3, 1],
    "demand_score": [0.1, 0.3, 0.5, 0.7, 0.9]
}

df = pd.DataFrame(data)

X = df[['hour', 'day_of_week', 'seats_remaining', 'time_to_match']]
y = df['demand_score']

model = RandomForestRegressor()
model.fit(X, y)

joblib.dump(model, "app/ml/demand_model.pkl")

print("✅ Model trained with dummy data")