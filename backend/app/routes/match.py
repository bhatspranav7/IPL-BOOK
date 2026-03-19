from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.match import Match
from app.services.match_service import create_match_with_seats

router = APIRouter()


@router.get("/matches")
def get_matches(db: Session = Depends(get_db)):
    matches = db.query(Match).all()
    return matches


@router.post("/create-match")
def create_match(
    team1: str,
    team2: str,
    stadium: str,
    date: str,
    seats: int,
    db: Session = Depends(get_db)
):
    return create_match_with_seats(
    db=db,
    team1=team1,
    team2=team2,
    stadium=stadium,
    date=date,
    total_seats=seats
)