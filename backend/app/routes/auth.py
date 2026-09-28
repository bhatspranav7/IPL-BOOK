from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin
from app.utils.auth import get_current_user, is_admin
from app.utils.security import hash_password, verify_password, create_token

router = APIRouter(tags=["Auth"])


def _token_response(user: User):
    return {
        "access_token": create_token({"user_id": user.id}),
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "email": user.email, "is_admin": is_admin(user)},
    }


@router.post("/register")
def register(data: UserCreate, db: Session = Depends(get_db)):

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=data.name.strip(),
        email=data.email,
        password=hash_password(data.password)
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)

    return {"message": "User created", **_token_response(user)}


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    # One message for both cases so the endpoint can't be used to enumerate emails
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return _token_response(user)


@router.get("/me")
def me(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return {"id": user.id, "name": user.name, "email": user.email, "is_admin": is_admin(user)}
