from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.match import Match
from app.models.seat import Seat
from app.schemas.payment_schema import MatchCreate
from app.services.booking_service import get_seat_map
from app.services.match_service import create_match_with_seats
from app.utils.auth import get_optional_user, require_admin

router = APIRouter(tags=["Matches"])


def _serialize(match: Match, total: int, booked: int):
    return {
        "id": match.id,
        "team1": match.team1,
        "team2": match.team2,
        "stadium": match.stadium,
        "date": match.date,
        "total_seats": total,
        "available_seats": total - booked,
    }


def _counts(db: Session, match_ids=None):
    q = db.query(
        Seat.match_id,
        func.count(Seat.id),
        func.count(Seat.id).filter(Seat.is_booked.is_(True))
    ).group_by(Seat.match_id)
    if match_ids is not None:
        q = q.filter(Seat.match_id.in_(match_ids))
    return {mid: (total, booked) for mid, total, booked in q}


@router.get("/matches")
def get_matches(db: Session = Depends(get_db)):
    matches = db.query(Match).order_by(Match.id.desc()).all()
    counts = _counts(db)
    return [_serialize(m, *counts.get(m.id, (0, 0))) for m in matches]


@router.get("/matches/{match_id}")
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    counts = _counts(db, [match_id])
    return _serialize(match, *counts.get(match_id, (0, 0)))


@router.get("/matches/{match_id}/seats")
def get_seats(match_id: int, db: Session = Depends(get_db), user_id=Depends(get_optional_user)):
    if not db.get(Match, match_id):
        raise HTTPException(status_code=404, detail="Match not found")
    return get_seat_map(db, match_id, user_id)


@router.get("/available-seats/{match_id}")
def available_seats(match_id: int, db: Session = Depends(get_db)):
    if not db.get(Match, match_id):
        raise HTTPException(status_code=404, detail="Match not found")
    seats = get_seat_map(db, match_id)
    return {
        "match_id": match_id,
        "available_seats": [s["seat"] for s in seats if s["status"] == "AVAILABLE"],
    }


@router.post("/create-match")
def create_match(
    data: MatchCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin)
):
    return create_match_with_seats(
        db=db,
        team1=data.team1,
        team2=data.team2,
        stadium=data.stadium,
        date=data.date,
        total_seats=data.seats
    )
