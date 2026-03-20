from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import hashlib

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    sha_password = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(sha_password)


def verify_password(plain_password: str, hashed_password: str):
    sha_password = hashlib.sha256(plain_password.encode()).hexdigest()
    return pwd_context.verify(sha_password, hashed_password)


def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=2)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)