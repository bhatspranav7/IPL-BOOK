from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 🔥 USE ENV VARIABLE (DOCKER READY)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ipldb"
)

# 🔹 Engine
engine = create_engine(
    DATABASE_URL,
    echo=True
)

# 🔹 Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 🔹 Base
Base = declarative_base()


# 🔹 Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔥 INIT DB
def init_db():
    import app.models.user
    import app.models.match
    import app.models.seat
    import app.models.booking
    import app.models.booking_logs

    Base.metadata.create_all(bind=engine)