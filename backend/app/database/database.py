from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./ipl.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# 🔹 DB SESSION DEPENDENCY (REQUIRED)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔹 INIT DB (CREATE TABLES)
def init_db():
    from app.models import user, match, seat, booking  # IMPORTANT
    Base.metadata.create_all(bind=engine)