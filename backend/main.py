from fastapi import FastAPI
from app.database.database import Base, engine

from app.routes import auth, match, booking

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(match.router)
app.include_router(booking.router)

@app.get("/")
def home():
    return {"message": "IPL Ticket Booking API"}