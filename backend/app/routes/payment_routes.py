from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.payment_service import (
    create_payment_intent,
    confirm_payment,
    fail_payment,
    get_payment_status
)
from app.utils.auth import get_current_user
from app.schemas.payment_schema import SeatRequest, PaymentConfirmRequest

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate-payment")
def initiate_payment(
    data: SeatRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return create_payment_intent(db, user_id, data.match_id, data.seats)


@router.post("/confirm-payment")
def confirm(
    data: PaymentConfirmRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return confirm_payment(db, data.payment_id, user_id)


@router.post("/fail-payment")
def fail(
    data: PaymentConfirmRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return fail_payment(db, data.payment_id, user_id)


@router.get("/status/{payment_id}")
def payment_status(
    payment_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return get_payment_status(db, payment_id, user_id)
