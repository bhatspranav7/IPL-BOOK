from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import User
from app.utils.security import hash_password, verify_password, create_token

router = APIRouter()


@router.post("/register")
def register(name: str, email: str, password: str, db: Session = Depends(get_db)):

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
def login(email: str, password: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Wrong password")

    token = create_token({"user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer"
    }