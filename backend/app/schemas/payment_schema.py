from pydantic import BaseModel, Field
from typing import List


class SeatRequest(BaseModel):
    match_id: int
    seats: List[str] = Field(min_length=1)


class PaymentConfirmRequest(BaseModel):
    payment_id: str


class MatchCreate(BaseModel):
    team1: str = Field(min_length=1, max_length=40)
    team2: str = Field(min_length=1, max_length=40)
    stadium: str = Field(min_length=1, max_length=80)
    date: str = Field(description="YYYY-MM-DD")
    seats: int = Field(default=50, ge=1, le=260)


class RaceRequest(BaseModel):
    match_id: int
    seat: str
