from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.utils.auth import get_current_user
from app.services.booking_service import validate_and_lock_seats

router = APIRouter(prefix="/booking", tags=["Booking"])


# 🔹 TEMPORARY VALIDATION ENDPOINT (OPTIONAL)
@router.post("/validate-seats")
def validate_seats(data: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        match_id = data["match_id"]
        seats = data["seats"]

        validate_and_lock_seats(db, match_id, seats)

        return {
            "message": "Seats locked successfully",
            "seats": seats
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))