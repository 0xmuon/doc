"""jwt helpers.token is only made after email and password already matched."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

from app.utils.exceptions import UnauthorizedException

load_dotenv()

# hs256 wants a long secret,so the default is already 32+ characters.
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-shopping-secret-key-32b")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def create_access_token(user_id: int, email: str, role: str) -> str:
    """put user id in sub.role is only a hint.password never goes inside the token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    # role in the token can go stale.routes read Role from the Users row instead.
    payload = {"sub": str(user_id), "email": email, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """bad signature and expired token both come back as 401."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise UnauthorizedException("Invalid or expired token")
