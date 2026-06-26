from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List
import asyncio

from app.models.seat import Seat
from app.models.booking_logs import BookingLog
from app.utils.redis_client import redis_client
from app.services.websocket_manager import manager
from app.services.kafka_producer import send_event


# =========================================================
# 🔹 LOGGER FUNCTION
# =========================================================
def log_booking(
    db: Session,
    match_id: int,
    seat_no: str,
    user_id: int,
    status: str,
    price: float = None
):
    log = BookingLog(
        match_id=match_id,
        seat_no=seat_no,
        user_id=user_id,
        status=status,
        price=price
    )
    db.add(log)
    db.commit()


# =========================================================
# 🔹 VALIDATE + LOCK SEATS
# =========================================================
def validate_and_lock_seats(
    db: Session,
    match_id: int,
    seats: List[str]
):

    locked_keys = []

    try:
        for seat_no in seats:

            lock_key = f"lock:{match_id}:{seat_no}"

            is_locked = redis_client.set(lock_key, "locked", nx=True, ex=120)

            if not is_locked:
                raise HTTPException(
                    status_code=400,
                    detail=f"{seat_no} is being booked by someone else"
                )

            locked_keys.append(lock_key)

            seat = db.query(Seat).filter(
                Seat.match_id == match_id,
                Seat.seat_number == seat_no
            ).first()

            if not seat:
                raise HTTPException(
                    status_code=404,
                    detail=f"{seat_no} not found"
                )

            if seat.is_booked:
                raise HTTPException(
                    status_code=400,
                    detail=f"{seat_no} already booked"
                )

        return True

    except Exception as e:
        for key in locked_keys:
            redis_client.delete(key)
        raise e


# =========================================================
# 🔹 CONFIRM BOOKING (🔥 UPDATED WITH KAFKA + WEBSOCKET)
# =========================================================
def confirm_booking(
    db: Session,
    match_id: int,
    seats: List[str],
    user_id: int,
    price: float
):
    for seat_no in seats:

        seat = db.query(Seat).filter(
            Seat.match_id == match_id,
            Seat.seat_number == seat_no
        ).first()

        if seat:
            seat.is_booked = True

        # ✅ LOG SUCCESS
        log_booking(
            db,
            match_id=match_id,
            seat_no=seat_no,
            user_id=user_id,
            status="SUCCESS",
            price=price
        )

        # 🔓 unlock
        lock_key = f"lock:{match_id}:{seat_no}"
        redis_client.delete(lock_key)

    db.commit()

    # 🔥 KAFKA EVENT (SUCCESS)
    send_event("booking-events", {
        "match_id": match_id,
        "user_id": user_id,
        "seats": seats,
        "price": price,
        "status": "SUCCESS"
    })

    # 🔥 REAL-TIME PRICE UPDATE BROADCAST
    try:
        asyncio.create_task(
            manager.broadcast({
                "event": "price_update",
                "match_id": match_id
            })
        )
    except Exception as e:
        print("WebSocket broadcast failed:", e)


# =========================================================
# 🔹 FAIL BOOKING (🔥 UPDATED WITH KAFKA)
# =========================================================
def fail_booking(
    db: Session,
    match_id: int,
    seats: List[str],
    user_id: int
):
    for seat_no in seats:

        log_booking(
            db,
            match_id=match_id,
            seat_no=seat_no,
            user_id=user_id,
            status="FAILED"
        )

        lock_key = f"lock:{match_id}:{seat_no}"
        redis_client.delete(lock_key)

    # 🔥 KAFKA EVENT (FAILED)
    send_event("booking-events", {
        "match_id": match_id,
        "user_id": user_id,
        "seats": seats,
        "status": "FAILED"
    })


# =========================================================
# 🔹 PENDING LOG (🔥 UPDATED WITH KAFKA)
# =========================================================
def log_pending_booking(
    db: Session,
    match_id: int,
    seats: List[str],
    user_id: int
):
    for seat_no in seats:
        log_booking(
            db,
            match_id=match_id,
            seat_no=seat_no,
            user_id=user_id,
            status="PENDING"
        )

    # 🔥 KAFKA EVENT (PENDING)
    send_event("booking-events", {
        "match_id": match_id,
        "user_id": user_id,
        "seats": seats,
        "status": "PENDING"
    })


# =========================================================
# 🔹 UNLOCK HELPER
# =========================================================
def unlock_seats(match_id: int, seats: List[str]):
    for seat_no in seats:
        key = f"lock:{match_id}:{seat_no}"
        redis_client.delete(key)