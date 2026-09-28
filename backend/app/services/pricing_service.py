from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.config import BASE_PRICE
from app.services.ml_service import predict_demand, MODEL_MAE
from app.models.seat import Seat
from app.models.match import Match

DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M")

# IPL evening games start 19:30 IST = 14:00 UTC
DEFAULT_START_UTC = timedelta(hours=14)


def parse_match_date(value: str) -> datetime | None:
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value.strip(), fmt)
        except (ValueError, AttributeError):
            continue
        if "%H" not in fmt:
            parsed += DEFAULT_START_UTC
        return parsed
    return None


def seat_counts(db: Session, match_id: int) -> tuple[int, int]:
    total, booked = db.query(
        func.count(Seat.id),
        func.count(Seat.id).filter(Seat.is_booked.is_(True))
    ).filter(Seat.match_id == match_id).one()
    return total, booked


def get_dynamic_price(db: Session, match_id: int):

    # 🔹 Get match
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        return {"error": "Match not found"}

    total_seats, booked_seats = seat_counts(db, match_id)
    seats_remaining = total_seats - booked_seats
    occupancy = booked_seats / total_seats if total_seats else 0.0

    # 🔹 Time to match (in hours)
    match_time = parse_match_date(match.date)
    if match_time is None:
        return {"error": f"Invalid date format in DB: {match.date}"}

    time_to_match = max((match_time - datetime.utcnow()).total_seconds() / 3600, 0)

    # 🔹 ML prediction
    demand = predict_demand(occupancy, time_to_match)

    # 🔹 Dynamic pricing
    dynamic_price = BASE_PRICE * (1 + demand)

    return {
        "match_id": match_id,
        "base_price": BASE_PRICE,
        "total_seats": total_seats,
        "seats_remaining": seats_remaining,
        "occupancy": round(occupancy, 3),
        "time_to_match_hours": round(time_to_match, 2),
        "demand_score": round(demand, 3),
        "dynamic_price": round(dynamic_price, 2),
        "model_mae": MODEL_MAE,
    }


def simulate_price(occupancy: float, hours_to_match: float):
    """What-if pricing for the UI slider; does not touch the DB."""
    occupancy = min(max(occupancy, 0.0), 1.0)
    hours_to_match = max(hours_to_match, 0.0)
    demand = predict_demand(occupancy, hours_to_match)
    return {
        "occupancy": occupancy,
        "time_to_match_hours": hours_to_match,
        "demand_score": round(demand, 3),
        "dynamic_price": round(BASE_PRICE * (1 + demand), 2),
    }
