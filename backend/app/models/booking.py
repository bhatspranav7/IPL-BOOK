from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    match_id = Column(Integer, ForeignKey("matches.id"))

    seat_numbers = Column(String, nullable=False)

    payment_id = Column(String, nullable=True)
    payment_status = Column(String, default="PENDING")  # PENDING / SUCCESS / FAILED

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")