from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.pricing_service import get_dynamic_price, simulate_price

router = APIRouter(tags=["Pricing (ML)"])


@router.get("/dynamic-price/{match_id}")
def dynamic_price(match_id: int, db: Session = Depends(get_db)):
    result = get_dynamic_price(db, match_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/price-simulate")
def price_simulate(
    occupancy: float = Query(ge=0, le=1),
    hours_to_match: float = Query(ge=0, le=24 * 60)
):
    return simulate_price(occupancy, hours_to_match)
