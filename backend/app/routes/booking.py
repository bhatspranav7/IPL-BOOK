from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.seat import Seat

router = APIRouter()


@router.post("/book-seat")
def book_seat(match_id: int, seats: list[str], db: Session = Depends(get_db)):
    booked_seats = []

    for seat_no in seats:
        seat = db.query(Seat).filter(
            Seat.match_id == match_id,
            Seat.seat_number == seat_no
        ).first()

        if not seat:
            raise HTTPException(status_code=404, detail=f"{seat_no} not found")

        if seat.is_booked:
            raise HTTPException(status_code=400, detail=f"{seat_no} already booked")

        seat.is_booked = True
        booked_seats.append(seat_no)

    db.commit()

    return {
        "message": "Seats booked successfully",
        "seats": booked_seats
    }