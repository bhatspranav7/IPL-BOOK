from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, ALGORITHM, ADMIN_EMAILS
from app.database.database import get_db
from app.models.user import User

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def _decode(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return _decode(credentials.credentials)


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(optional_security)):
    if credentials is None:
        return None
    try:
        return _decode(credentials.credentials)
    except HTTPException:
        return None


def is_admin(user: User) -> bool:
    return not ADMIN_EMAILS or user.email.lower() in ADMIN_EMAILS


def require_admin(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admins only")
    return user_id
