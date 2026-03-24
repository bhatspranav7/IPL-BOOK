from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import init_db
from app.routes import auth, match, booking, payment_routes, websocket, ml_routes
from app.routes import agent_routes
# 🔹 Create app FIRST
app = FastAPI()
app.include_router(agent_routes.router)

# 🔹 CORS (important for future frontend / agents)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change later in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 Initialize DB (creates all tables)
init_db()

# 🔹 Register routers
app.include_router(auth.router)
app.include_router(match.router)
app.include_router(booking.router)
app.include_router(payment_routes.router)
app.include_router(websocket.router)
app.include_router(ml_routes.router)


# 🔹 Health check (very useful)
@app.get("/")
def root():
    return {"message": "IPL Booking System + ML running 🚀"}