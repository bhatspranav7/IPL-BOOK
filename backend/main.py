from fastapi import FastAPI
from app.database.database import Base, engine

from app.routes import auth, match, booking, websocket

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Register routes
app.include_router(auth.router)
app.include_router(match.router)
app.include_router(booking.router)
app.include_router(websocket.router)  # ✅ NEW

@app.get("/")
def home():
    return {"message": "IPL Ticket Booking API"}