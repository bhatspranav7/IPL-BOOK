from sqlalchemy.orm import Session
from sqlalchemy import update
from fastapi import HTTPException
from typing import List

from app.config import LOCK_TTL_SECONDS, MAX_SEATS_PER_BOOKING
from app.models.seat import Seat
from app.models.match import Match
from app.models.booking_logs import BookingLog
from app.utils.redis_client import redis_client, REDIS_MODE
from app.services.websocket_manager import manager
from app.services.kafka_producer import send_event

# Compare-and-delete: only the lock owner may release a lock
_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


def lock_key(match_id: int, seat_no: str) -> str:
    return f"lock:{match_id}:{seat_no}"


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
    db.add(BookingLog(
        match_id=match_id,
        seat_no=seat_no,
        user_id=user_id,
        status=status,
        price=price
    ))


def _emit(event: str, match_id: int, seats: List[str], user_id: int, **extra):
    payload = {"event": event, "match_id": match_id, "seats": seats, "user_id": user_id, **extra}
    send_event("booking-events", payload)
    manager.publish(payload)


# =========================================================
# 🔹 SEAT MAP (DB state + live Redis locks)
# =========================================================
def get_seat_map(db: Session, match_id: int, user_id: int | None = None):
    seats = (
        db.query(Seat)
        .filter(Seat.match_id == match_id)
        .order_by(Seat.id)
        .all()
    )
    if not seats:
        return []

    owners = redis_client.mget([lock_key(match_id, s.seat_number) for s in seats])

    result = []
    for seat, owner in zip(seats, owners):
        if seat.is_booked:
            status = "BOOKED"
        elif owner is not None:
            status = "LOCKED"
        else:
            status = "AVAILABLE"
        result.append({
            "seat": seat.seat_number,
            "status": status,
            "mine": owner is not None and user_id is not None and owner == str(user_id),
        })
    return result


# =========================================================
# 🔹 VALIDATE + LOCK SEATS
# =========================================================
def validate_and_lock_seats(
    db: Session,
    match_id: int,
    seats: List[str],
    user_id: int
):
    seats = list(dict.fromkeys(s.strip().upper() for s in seats if s.strip()))

    if not seats:
        raise HTTPException(status_code=400, detail="Select at least one seat")
    if len(seats) > MAX_SEATS_PER_BOOKING:
        raise HTTPException(status_code=400, detail=f"Max {MAX_SEATS_PER_BOOKING} seats per booking")

    # Cheap DB checks first so we never hold a lock for an invalid seat
    rows = {
        s.seat_number: s
        for s in db.query(Seat).filter(Seat.match_id == match_id, Seat.seat_number.in_(seats))
    }
    for seat_no in seats:
        if seat_no not in rows:
            raise HTTPException(status_code=404, detail=f"{seat_no} not found")
        if rows[seat_no].is_booked:
            raise HTTPException(status_code=409, detail=f"{seat_no} already booked")

    locked_keys = []
    owner = str(user_id)

    try:
        for seat_no in seats:
            key = lock_key(match_id, seat_no)

            # SET NX EX is atomic: exactly one concurrent caller wins the seat
            if redis_client.set(key, owner, nx=True, ex=LOCK_TTL_SECONDS):
                locked_keys.append(key)
                continue

            if redis_client.get(key) == owner:
                # Re-locking your own seat just refreshes the TTL
                redis_client.expire(key, LOCK_TTL_SECONDS)
                continue

            raise HTTPException(
                status_code=409,
                detail=f"{seat_no} is being booked by someone else"
            )

    except Exception:
        for key in locked_keys:
            redis_client.delete(key)
        raise

    for seat_no in seats:
        log_booking(db, match_id, seat_no, user_id, "LOCKED")
    db.commit()

    _emit("seats_locked", match_id, seats, user_id, ttl=LOCK_TTL_SECONDS)

    return {"seats": seats, "expires_in": LOCK_TTL_SECONDS}


# =========================================================
# 🔹 LOCK HELPERS
# =========================================================
def release_if_owner(match_id: int, seat_no: str, user_id: int) -> bool:
    key = lock_key(match_id, seat_no)
    if REDIS_MODE == "redis":
        return bool(redis_client.eval(_RELEASE_SCRIPT, 1, key, str(user_id)))
    if redis_client.get(key) == str(user_id):
        return bool(redis_client.delete(key))
    return False


def release_seats(match_id: int, seats: List[str], user_id: int, emit: bool = True):
    released = [s for s in seats if release_if_owner(match_id, s, user_id)]
    if released and emit:
        _emit("seats_released", match_id, released, user_id)
    return released


def locks_held(match_id: int, seats: List[str], user_id: int) -> bool:
    owners = redis_client.mget([lock_key(match_id, s) for s in seats])
    return all(o == str(user_id) for o in owners)


def extend_locks(match_id: int, seats: List[str], ttl: int):
    for seat_no in seats:
        redis_client.expire(lock_key(match_id, seat_no), ttl)


def lock_ttl(match_id: int, seats: List[str]) -> int:
    ttls = [redis_client.ttl(lock_key(match_id, s)) for s in seats]
    live = [t for t in ttls if t is not None and t >= 0]
    return min(live) if len(live) == len(seats) else 0


# =========================================================
# 🔹 CONFIRM BOOKING
# =========================================================
def confirm_booking(
    db: Session,
    match_id: int,
    seats: List[str],
    user_id: int,
    price: float
):
    # Second line of defence: conditional UPDATE only flips seats that are still
    # free, so even a lost Redis lock can never produce a double booking.
    result = db.execute(
        update(Seat)
        .where(
            Seat.match_id == match_id,
            Seat.seat_number.in_(seats),
            Seat.is_booked.is_(False)
        )
        .values(is_booked=True)
    )

    if result.rowcount != len(seats):
        db.rollback()
        raise HTTPException(status_code=409, detail="One or more seats were already booked")

    match = db.get(Match, match_id)
    if match is not None and match.available_seats is not None:
        match.available_seats = max(match.available_seats - len(seats), 0)

    for seat_no in seats:
        log_booking(db, match_id, seat_no, user_id, "SUCCESS", price)


# =========================================================
# 🔹 FAIL BOOKING
# =========================================================
def fail_booking(
    db: Session,
    match_id: int,
    seats: List[str],
    user_id: int
):
    for seat_no in seats:
        log_booking(db, match_id, seat_no, user_id, "FAILED")
