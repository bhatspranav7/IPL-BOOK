import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:newpassword@localhost:5432/ipldb"

engine = create_engine(DATABASE_URL)

# 🔹 Load booking logs
logs = pd.read_sql("SELECT * FROM booking_logs", engine)

# 🔹 Load seats
seats = pd.read_sql("SELECT * FROM seats", engine)

# 🔹 Convert time
logs['booking_time'] = pd.to_datetime(logs['booking_time'])

# 🔹 Feature 1: time-based
logs['hour'] = logs['booking_time'].dt.hour
logs['day_of_week'] = logs['booking_time'].dt.dayofweek

# 🔹 Feature 2: seats remaining per match
total_seats = seats.groupby('match_id').size().reset_index(name='total_seats')

booked_seats = logs[logs['status'] == "SUCCESS"].groupby('match_id').size().reset_index(name='booked_seats')

merged = logs.merge(total_seats, on='match_id', how='left')
merged = merged.merge(booked_seats, on='match_id', how='left')

merged['booked_seats'] = merged['booked_seats'].fillna(0)

merged['seats_remaining'] = merged['total_seats'] - merged['booked_seats']

# 🔹 Feature 3: time to match (TEMP — we improve later)
merged['time_to_match'] = 5  # placeholder for now

# 🔹 Target
merged['demand_score'] = merged['status'].apply(lambda x: 1 if x == "SUCCESS" else 0)

# 🔹 Save
merged.to_csv("app/ml/booking_data.csv", index=False)

print("✅ REAL data exported!")