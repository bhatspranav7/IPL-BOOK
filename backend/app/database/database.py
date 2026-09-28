from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL, SQL_ECHO

# 🔹 Engine
engine = create_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    pool_pre_ping=True
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

    # create_all never alters existing tables, so add columns introduced later
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS amount FLOAT"))
