from fastapi import FastAPI

from app.routes import auth, match, booking, websocket, payment_routes
from app.database.database import init_db

app = FastAPI()


# 🔥 CREATE TABLES ON STARTUP
init_db()


# ROUTES
app.include_router(auth.router)
app.include_router(match.router)
app.include_router(booking.router)
app.include_router(payment_routes.router)
app.include_router(websocket.router)


@app.get("/")
def home():
    return {"message": "IPL Booking API Running"}