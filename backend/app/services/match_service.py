import string

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.seat import Seat
from app.services.pricing_service import parse_match_date

SEATS_PER_ROW = 10
MAX_SEATS = SEATS_PER_ROW * len(string.ascii_uppercase)


def create_match_with_seats(
    db: Session,
    team1: str,
    team2: str,
    stadium: str,
    date: str,
    total_seats: int = 50
):
    team1, team2, stadium = team1.strip(), team2.strip(), stadium.strip()
    if not team1 or not team2 or not stadium:
        raise HTTPException(status_code=400, detail="Teams and stadium are required")
    if team1.lower() == team2.lower():
        raise HTTPException(status_code=400, detail="A team cannot play itself")
    if not 1 <= total_seats <= MAX_SEATS:
        raise HTTPException(status_code=400, detail=f"Seats must be between 1 and {MAX_SEATS}")
    if parse_match_date(date) is None:
        raise HTTPException(status_code=400, detail="Date must be YYYY-MM-DD")

    match = Match(
        team1=team1,
        team2=team2,
        stadium=stadium,
        date=date.strip(),
        total_seats=total_seats,
        available_seats=total_seats
    )

    db.add(match)
    db.flush()

    # Generate seats: rows A, B, C ... with 10 seats each
    db.add_all([
        Seat(
            match_id=match.id,
            seat_number=f"{string.ascii_uppercase[i // SEATS_PER_ROW]}{i % SEATS_PER_ROW + 1}",
            is_booked=False
        )
        for i in range(total_seats)
    ])
    db.commit()

    return {
        "message": "Match created with seats",
        "match_id": match.id
    }
