from sqlalchemy import Column, Integer, String
from app.database.db import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    team1 = Column(String)
    team2 = Column(String)
    stadium = Column(String)
    date = Column(String)
    total_seats = Column(Integer)
    available_seats = Column(Integer)