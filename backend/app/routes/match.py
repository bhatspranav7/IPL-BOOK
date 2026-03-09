from fastapi import APIRouter
from app.database.db import SessionLocal
from app.models.match import Match

router = APIRouter()

@router.get("/matches")
def get_matches():

    db = SessionLocal()

    matches = db.query(Match).all()

    return matches