from pydantic import BaseModel
from typing import List


class SeatRequest(BaseModel):
    match_id: int
    seats: List[str]


class PaymentConfirmRequest(BaseModel):
    payment_id: str