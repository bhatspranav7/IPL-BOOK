import os
import secrets


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ipldb")
    # Render / Heroku hand out postgres:// which SQLAlchemy 2 rejects
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


DATABASE_URL = _database_url()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "")

# A random fallback keeps local dev working but invalidates tokens on restart,
# so production must set SECRET_KEY.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "12"))

# Comma separated. Empty means every logged-in user may create matches (demo mode).
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

LOCK_TTL_SECONDS = int(os.getenv("LOCK_TTL_SECONDS", "120"))
PAYMENT_TTL_SECONDS = int(os.getenv("PAYMENT_TTL_SECONDS", "300"))
MAX_SEATS_PER_BOOKING = int(os.getenv("MAX_SEATS_PER_BOOKING", "6"))
BASE_PRICE = float(os.getenv("BASE_PRICE", "1000"))

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"
FRONTEND_DIR = os.getenv("FRONTEND_DIR", os.path.join(os.path.dirname(__file__), "..", "static"))
