"""
Auth utilities — JWT token creation/verification + password hashing.
Dependencies: pip install python-jose[cryptography] passlib[bcrypt]
"""

import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY  = os.getenv("JWT_SECRET_KEY", "change-this-in-production-please")
ALGORITHM   = "HS256"
TOKEN_HOURS = 24   # JWT expires after 24 hours

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password ──────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────
def create_token(client_id: str, email: str, is_super_admin: bool) -> str:
    payload = {
        "sub":            client_id,
        "email":          email,
        "is_super_admin": is_super_admin,
        "exp":            datetime.utcnow() + timedelta(hours=TOKEN_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Returns payload dict or None if invalid/expired."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None