from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password, verify_password, create_token

router = APIRouter()

@router.post("/register")
def register(name: str, email: str, password: str):

    db: Session = SessionLocal()

    hashed_password = hash_password(password)

    user = User(
        name=name,
        email=email,
        password=hashed_password
    )

    db.add(user)
    db.commit()

    return {"message": "User created"}


@router.post("/login")
def login(email: str, password: str):

    db: Session = SessionLocal()

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return {"error": "User not found"}

    if not verify_password(password, user.password):
        return {"error": "Wrong password"}

    token = create_token({"user_id": user.id})

    return {"access_token": token}