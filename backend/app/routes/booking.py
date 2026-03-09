from fastapi import APIRouter
from app.database.db import SessionLocal
from app.models.booking import Booking
from app.models.match import Match

router = APIRouter()

@router.post("/book-ticket")
def book_ticket(match_id:int, seats:int, user_id:int):

    db = SessionLocal()

    match = db.query(Match).filter(Match.id == match_id).first()

    if match.available_seats < seats:
        return {"error":"Not enough seats"}

    match.available_seats -= seats

    booking = Booking(
        user_id=user_id,
        match_id=match_id,
        seats=seats
    )

    db.add(booking)
    db.commit()

    return {"message":"Ticket booked"}