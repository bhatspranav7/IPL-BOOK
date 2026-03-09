from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.models.user import User

router = APIRouter()

@router.post("/register")
def register(name:str, email:str, password:str):

    db: Session = SessionLocal()

    user = User(
        name=name,
        email=email,
        password=password
    )

    db.add(user)
    db.commit()

    return {"message":"User created"}