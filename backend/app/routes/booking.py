from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.payment_schema import SeatRequest
from app.utils.auth import get_current_user
from app.services.booking_service import validate_and_lock_seats, release_seats
from app.services.payment_service import list_user_bookings

router = APIRouter(prefix="/booking", tags=["Booking"])


# 🔹 VALIDATE + LOCK (Redis SET NX with TTL)
@router.post("/validate-seats")
def validate_seats(data: SeatRequest, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):

    result = validate_and_lock_seats(db, data.match_id, data.seats, user_id)

    return {
        "message": "Seats locked successfully",
        **result
    }


# 🔹 RELEASE LOCKS (user changed their mind)
@router.post("/release")
def release(data: SeatRequest, user_id: int = Depends(get_current_user)):
    seats = [s.strip().upper() for s in data.seats]
    return {"released": release_seats(data.match_id, seats, user_id)}


# 🔹 MY BOOKINGS
@router.get("/me")
def my_bookings(db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    return list_user_bookings(db, user_id)
