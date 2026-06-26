from sqlalchemy.orm import Session
from datetime import datetime

from app.services.ml_service import predict_demand
from app.models.seat import Seat
from app.models.match import Match

BASE_PRICE = 1000


def get_dynamic_price(db: Session, match_id: int):

    # 🔹 Get match
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        return {"error": "Match not found"}

    # 🔹 Total seats
    total_seats = db.query(Seat).filter(Seat.match_id == match_id).count()

    # 🔹 Booked seats
    booked_seats = db.query(Seat).filter(
        Seat.match_id == match_id,
        Seat.is_booked == True
    ).count()

    seats_remaining = total_seats - booked_seats

    # 🔹 Time to match (in hours)
    now = datetime.utcnow()

    # ✅ FIX: convert string → datetime
    try:
        match_time = datetime.strptime(match.date, "%d-%m-%Y")
    except Exception:
        return {"error": "Invalid date format in DB"}

    time_to_match = (match_time - now).total_seconds() / 3600
    time_to_match = max(time_to_match, 0)

    # 🔹 ML prediction
    demand = predict_demand(seats_remaining, time_to_match)

    # 🔹 Dynamic pricing
    dynamic_price = BASE_PRICE * (1 + demand)

    return {
        "match_id": match_id,
        "seats_remaining": seats_remaining,
        "time_to_match_hours": round(time_to_match, 2),
        "demand_score": round(demand, 3),
        "dynamic_price": round(dynamic_price, 2)
    }