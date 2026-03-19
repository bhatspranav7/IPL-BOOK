from sqlalchemy import Column, Integer, String
from app.database.database import Base
from sqlalchemy.orm import relationship


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    seats = relationship("Seat", back_populates="match")
    team1 = Column(String)
    team2 = Column(String)
    stadium = Column(String)
    date = Column(String)
    total_seats = Column(Integer)
    available_seats = Column(Integer)