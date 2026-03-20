from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.seat import Seat
from app.utils.redis_client import redis_client

router = APIRouter()


@router.post("/book-seat")
def book_seat(match_id: int, seats: list[str], db: Session = Depends(get_db)):

    locked_keys = []

    try:
        for seat_no in seats:

            lock_key = f"lock:{match_id}:{seat_no}"

            # Try acquiring lock
            is_locked = redis_client.set(lock_key, "locked", nx=True, ex=120)

            if not is_locked:
                raise HTTPException(
                    status_code=400,
                    detail=f"{seat_no} is currently being booked by someone else"
                )

            locked_keys.append(lock_key)

            # DB check
            seat = db.query(Seat).filter(
                Seat.match_id == match_id,
                Seat.seat_number == seat_no
            ).first()

            if not seat:
                raise HTTPException(status_code=404, detail=f"{seat_no} not found")

            if seat.is_booked:
                raise HTTPException(status_code=400, detail=f"{seat_no} already booked")

            seat.is_booked = True

        db.commit()

        return {
            "message": "Seats booked successfully",
            "seats": seats
        }

    except Exception as e:
        db.rollback()
        raise e

    finally:
        # Release locks
        for key in locked_keys:
            redis_client.delete(key)