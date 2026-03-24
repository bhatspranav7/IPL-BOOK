from sqlalchemy import Column, Integer, String, DateTime, Float
from app.database.database import Base
from datetime import datetime

class BookingLog(Base):
    __tablename__ = "booking_logs"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer)
    seat_no = Column(String)
    user_id = Column(Integer)
    status = Column(String)
    price = Column(Float)
    booking_time = Column(DateTime, default=datetime.utcnow)