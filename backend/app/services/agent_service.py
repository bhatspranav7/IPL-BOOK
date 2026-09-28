"""Seat-picking agent.

Scores every contiguous block of free seats in a row (centre of the row and
rows closer to the pitch score higher), then drives the normal booking flow:
lock -> initiate payment. It uses the exact same code path as a human user,
so it gets the same concurrency guarantees.
"""
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.booking_service import get_seat_map, validate_and_lock_seats
from app.services.payment_service import create_payment_intent

_SEAT_RE = re.compile(r"^([A-Z]+)(\d+)$")


def _rows(seat_map):
    rows: dict[str, list[tuple[int, dict]]] = {}
    for s in seat_map:
        m = _SEAT_RE.match(s["seat"])
        if m:
            rows.setdefault(m.group(1), []).append((int(m.group(2)), s))
    for row in rows.values():
        row.sort(key=lambda x: x[0])
    return dict(sorted(rows.items()))


def rank_blocks(seat_map, count: int):
    rows = _rows(seat_map)
    row_names = list(rows)
    candidates = []

    for row_index, row_name in enumerate(row_names):
        row = rows[row_name]
        width = max(n for n, _ in row)
        centre = (width + 1) / 2
        row_score = 1 - row_index / max(len(row_names), 1)

        for i in range(len(row) - count + 1):
            block = row[i:i + count]
            numbers = [n for n, _ in block]
            contiguous = numbers[-1] - numbers[0] == count - 1
            free = all(s["status"] == "AVAILABLE" for _, s in block)
            if not (contiguous and free):
                continue

            mid = sum(numbers) / count
            centre_score = 1 - abs(mid - centre) / max(centre, 1)
            score = 0.6 * centre_score + 0.4 * row_score
            candidates.append({
                "seats": [s["seat"] for _, s in block],
                "score": round(score, 3),
                "centre_score": round(centre_score, 3),
                "row_score": round(row_score, 3),
            })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates


def auto_book_best_seats(db: Session, match_id: int, user_id: int, count: int = 2):

    seat_map = get_seat_map(db, match_id, user_id)
    if not seat_map:
        raise HTTPException(status_code=404, detail="Match not found")

    candidates = rank_blocks(seat_map, count)
    if not candidates:
        raise HTTPException(status_code=409, detail=f"No block of {count} adjacent seats available")

    trace = []
    # Another user may grab our first choice between ranking and locking,
    # so fall through to the next-best block on conflict.
    for candidate in candidates[:5]:
        try:
            validate_and_lock_seats(db, match_id, candidate["seats"], user_id)
        except HTTPException as e:
            trace.append({"seats": candidate["seats"], "result": e.detail})
            continue

        trace.append({"seats": candidate["seats"], "result": "locked"})
        payment = create_payment_intent(db, user_id, match_id, candidate["seats"])
        return {
            "selected_seats": candidate["seats"],
            "reasoning": candidate,
            "alternatives": candidates[1:4],
            "trace": trace,
            "booking_response": payment,
        }

    raise HTTPException(status_code=409, detail={"message": "All top seat blocks were taken", "trace": trace})
