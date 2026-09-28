from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.agent_service import auto_book_best_seats
from app.utils.auth import get_current_user

router = APIRouter(tags=["AI Agent"])


@router.post("/ai-book/{match_id}")
def ai_book(
    match_id: int,
    count: int = Query(default=2, ge=1, le=6),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return auto_book_best_seats(db, match_id, user_id, count)
