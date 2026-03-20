from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.utils.auth import get_current_user
from app.services.booking_service import book_seats_service
from app.models.booking import Booking

router = APIRouter()


# 🔥 BOOK SEATS (NOW CLEAN — SERVICE LAYER)
@router.post("/book-seat")
def book_seat(
    match_id: int,
    seats: list[str],
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return book_seats_service(db, match_id, seats, user_id)


# 🔥 GET MY BOOKINGS (LEVEL 5)
@router.get("/my-bookings")
def get_my_bookings(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    bookings = db.query(Booking).filter(
        Booking.user_id == user_id
    ).all()

    return [
        {
            "match_id": b.match_id,
            "seat_number": b.seat_number
        }
        for b in bookings
    ]