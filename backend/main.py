import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import CORS_ORIGINS, FRONTEND_DIR, LOCK_TTL_SECONDS
from app.database.database import init_db, engine
from app.routes import auth, match, booking, payment_routes, websocket, ml_routes, agent_routes, lab_routes
from app.services.kafka_producer import kafka_enabled
from app.services.ml_service import MODEL_MAE
from app.utils.redis_client import REDIS_MODE

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="IPL Ticket Booking",
    description="Redis seat locking · two-phase payments · ML dynamic pricing",
    version="2.0.0",
)

# 🔹 CORS (only needed when the frontend is hosted on another origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials="*" not in CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 Initialize DB (creates all tables)
init_db()

# 🔹 Register routers. Each is served at the root (Swagger / original demo)
# and under /api (used by the frontend), the latter hidden from the docs.
ROUTERS = [
    auth.router,
    match.router,
    booking.router,
    payment_routes.router,
    websocket.router,
    ml_routes.router,
    agent_routes.router,
    lab_routes.router,
]
for r in ROUTERS:
    app.include_router(r)
    app.include_router(r, prefix="/api", include_in_schema=False)


@app.get("/health", tags=["System"])
@app.get("/api/health", include_in_schema=False)
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "postgres" if db_ok else "unreachable",
        "lock_backend": REDIS_MODE,
        "kafka": "enabled" if kafka_enabled() else "disabled",
        "lock_ttl_seconds": LOCK_TTL_SECONDS,
        "model_mae": MODEL_MAE,
    }


# 🔹 Serve the built React app when present (single-service deployment)
_frontend = os.path.abspath(FRONTEND_DIR)
_index = os.path.join(_frontend, "index.html")

if os.path.isfile(_index):
    app.mount("/assets", StaticFiles(directory=os.path.join(_frontend, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith(("api/", "ws/")):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = os.path.abspath(os.path.join(_frontend, full_path))
        if full_path and candidate.startswith(_frontend + os.sep) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(_index)
else:
    @app.get("/")
    def root():
        return {"message": "IPL Booking System + ML running 🚀", "docs": "/docs"}
