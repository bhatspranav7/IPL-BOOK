from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    seat_number = Column(String, index=True)  # A1, A2, B3
    is_booked = Column(Boolean, default=False)

    match = relationship("Match", back_populates="seats")