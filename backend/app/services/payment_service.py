import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import PAYMENT_TTL_SECONDS
from app.models.booking import Booking
from app.models.match import Match
from app.services.booking_service import (
    locks_held,
    extend_locks,
    lock_ttl,
    confirm_booking,
    fail_booking,
    release_seats,
    _emit,
)
from app.services.pricing_service import get_dynamic_price


def _serialize(booking: Booking, match: Match | None = None, expires_in: int | None = None):
    data = {
        "payment_id": booking.payment_id,
        "status": booking.payment_status,
        "match_id": booking.match_id,
        "seats": booking.seat_numbers.split(","),
        "amount": booking.amount,
        "created_at": booking.created_at,
    }
    if match is not None:
        data["match"] = {
            "team1": match.team1,
            "team2": match.team2,
            "stadium": match.stadium,
            "date": match.date,
        }
    if expires_in is not None:
        data["expires_in"] = expires_in
    return data


def _get_owned(db: Session, payment_id: str, user_id: int) -> Booking:
    booking = db.query(Booking).filter(Booking.payment_id == payment_id).first()

    # Same error for "missing" and "not yours" so payment ids can't be probed
    if not booking or booking.user_id != user_id:
        raise HTTPException(status_code=404, detail="Invalid payment_id")
    return booking


# 🔹 STEP 1: CREATE PAYMENT INTENT
def create_payment_intent(db: Session, user_id: int, match_id: int, seats: list[str]):

    seats = list(dict.fromkeys(s.strip().upper() for s in seats if s.strip()))
    if not seats:
        raise HTTPException(status_code=400, detail="Select at least one seat")

    # Payment is only allowed on seats this user currently holds
    if not locks_held(match_id, seats, user_id):
        raise HTTPException(
            status_code=409,
            detail="Seat lock missing or expired - lock the seats again"
        )

    pricing = get_dynamic_price(db, match_id)
    if "error" in pricing:
        raise HTTPException(status_code=404, detail=pricing["error"])

    # Give the user time to pay without losing the seats
    extend_locks(match_id, seats, PAYMENT_TTL_SECONDS)

    payment_id = str(uuid.uuid4())

    booking = Booking(
        user_id=user_id,
        match_id=match_id,
        seat_numbers=",".join(seats),
        payment_id=payment_id,
        payment_status="PENDING",
        amount=round(pricing["dynamic_price"] * len(seats), 2)
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    _emit("payment_pending", match_id, seats, user_id, payment_id=payment_id)

    return {
        **_serialize(booking, expires_in=PAYMENT_TTL_SECONDS),
        "price_per_seat": pricing["dynamic_price"],
    }


# 🔹 STEP 2: CONFIRM PAYMENT
def confirm_payment(db: Session, payment_id: str, user_id: int):

    booking = _get_owned(db, payment_id, user_id)

    if booking.payment_status == "SUCCESS":
        return {**_serialize(booking), "message": "Already confirmed"}

    if booking.payment_status == "FAILED":
        raise HTTPException(status_code=409, detail="Payment already failed - start a new booking")

    seats = booking.seat_numbers.split(",")

    if not locks_held(booking.match_id, seats, user_id):
        booking.payment_status = "FAILED"
        fail_booking(db, booking.match_id, seats, user_id)
        db.commit()
        _emit("payment_failed", booking.match_id, seats, user_id, reason="lock_expired")
        raise HTTPException(status_code=409, detail="Seat lock expired before payment")

    per_seat = (booking.amount or 0) / len(seats)
    try:
        confirm_booking(db, booking.match_id, seats, user_id, per_seat)
    except HTTPException:
        booking.payment_status = "FAILED"
        fail_booking(db, booking.match_id, seats, user_id)
        db.commit()
        release_seats(booking.match_id, seats, user_id)
        raise
    booking.payment_status = "SUCCESS"
    db.commit()

    # 🔓 Unlock seats (they are now permanently booked in Postgres)
    release_seats(booking.match_id, seats, user_id, emit=False)
    _emit("seats_booked", booking.match_id, seats, user_id, payment_id=payment_id)

    return _serialize(booking)


# 🔹 STEP 3: FAIL PAYMENT
def fail_payment(db: Session, payment_id: str, user_id: int):

    booking = _get_owned(db, payment_id, user_id)

    if booking.payment_status == "SUCCESS":
        raise HTTPException(status_code=409, detail="Payment already succeeded")

    seats = booking.seat_numbers.split(",")

    if booking.payment_status != "FAILED":
        booking.payment_status = "FAILED"
        fail_booking(db, booking.match_id, seats, user_id)
        db.commit()

    # 🔓 Unlock seats so others can book them
    release_seats(booking.match_id, seats, user_id, emit=False)
    _emit("payment_failed", booking.match_id, seats, user_id, payment_id=payment_id)

    return _serialize(booking)


# 🔹 STEP 4: GET PAYMENT STATUS
def get_payment_status(db: Session, payment_id: str, user_id: int):

    booking = _get_owned(db, payment_id, user_id)
    seats = booking.seat_numbers.split(",")
    expires_in = lock_ttl(booking.match_id, seats) if booking.payment_status == "PENDING" else None
    return _serialize(booking, db.get(Match, booking.match_id), expires_in)


def list_user_bookings(db: Session, user_id: int):
    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc())
        .limit(100)
        .all()
    )
    matches = {m.id: m for m in db.query(Match).filter(Match.id.in_({b.match_id for b in bookings}))}
    return [_serialize(b, matches.get(b.match_id)) for b in bookings]
