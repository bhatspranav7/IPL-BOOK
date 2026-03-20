import uuid
from sqlalchemy.orm import Session
from app.models.booking import Booking
from app.models.seat import Seat
from app.services.booking_service import validate_and_lock_seats, unlock_seats
from app.services.websocket_manager import manager


# 🔹 STEP 1: CREATE PAYMENT INTENT
def create_payment_intent(db: Session, user_id: int, match_id: int, seats: list[str]):

    # Validate + Lock seats
    validate_and_lock_seats(db, match_id, seats)

    payment_id = str(uuid.uuid4())

    booking = Booking(
        user_id=user_id,
        match_id=match_id,
        seat_numbers=",".join(seats),
        payment_id=payment_id,
        payment_status="PENDING"
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {
        "payment_id": payment_id,
        "status": "PENDING"
    }


# 🔹 STEP 2: CONFIRM PAYMENT
def confirm_payment(db: Session, payment_id: str):

    booking = db.query(Booking).filter(Booking.payment_id == payment_id).first()

    if not booking:
        raise Exception("Invalid payment_id")

    if booking.payment_status == "SUCCESS":
        return {"message": "Already confirmed"}

    seats = booking.seat_numbers.split(",")

    try:
        for seat_no in seats:
            seat = db.query(Seat).filter(
                Seat.match_id == booking.match_id,
                Seat.seat_number == seat_no
            ).first()

            if not seat:
                raise Exception(f"{seat_no} not found")

            if seat.is_booked:
                raise Exception(f"{seat_no} already booked")

            seat.is_booked = True

        booking.payment_status = "SUCCESS"

        db.commit()

        # 🔓 Unlock seats
        unlock_seats(booking.match_id, seats)

        # 🔥 WebSocket broadcast
        manager.broadcast({
            "event": "seat_booked",
            "match_id": booking.match_id,
            "seats": seats
        })

        return {"status": "SUCCESS"}

    except Exception as e:
        db.rollback()
        raise e


# 🔹 STEP 3: FAIL PAYMENT
def fail_payment(db: Session, payment_id: str):

    booking = db.query(Booking).filter(Booking.payment_id == payment_id).first()

    if not booking:
        raise Exception("Invalid payment_id")

    seats = booking.seat_numbers.split(",")

    booking.payment_status = "FAILED"
    db.commit()

    # 🔓 Unlock seats
    unlock_seats(booking.match_id, seats)

    return {"status": "FAILED"}


# 🔹 STEP 4: GET PAYMENT STATUS
def get_payment_status(db: Session, payment_id: str):

    booking = db.query(Booking).filter(Booking.payment_id == payment_id).first()

    if not booking:
        raise Exception("Invalid payment_id")

    return {
        "payment_id": booking.payment_id,
        "status": booking.payment_status,
        "match_id": booking.match_id,
        "seats": booking.seat_numbers.split(","),
        "created_at": booking.created_at
    }