from passlib.context import CryptContext
from sqlalchemy import String

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def validate_hash(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def generate_hash(password: str | String) -> str:
    return pwd_context.hash(password)
