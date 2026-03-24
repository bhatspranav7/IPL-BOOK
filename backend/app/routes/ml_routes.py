from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.pricing_service import get_dynamic_price

router = APIRouter()


@router.get("/dynamic-price/{match_id}")
def dynamic_price(match_id: int, db: Session = Depends(get_db)):
    return get_dynamic_price(db, match_id)