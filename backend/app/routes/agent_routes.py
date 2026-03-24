from fastapi import APIRouter
from app.services.agent_service import auto_book_best_seats

router = APIRouter()

@router.get("/ai-book/{match_id}")
def ai_book(match_id: int):
    return auto_book_best_seats(match_id)