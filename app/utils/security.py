"""jwt helpers.access and refresh are different types,and one cannot be used as the other."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

from app.utils import UnauthorizedException

load_dotenv()

# hs256 wants a long secret,so the default is already 32+ characters.
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-shopping-secret-key-32b")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))


def _encode(user_id: int, email: str, role: str, token_type: str, expire: datetime) -> str:
    # role in the token can go stale.routes read Role from the Users row instead.
    payload = {"sub": str(user_id), "email": email, "role": role, "type": token_type, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: int, email: str, role: str) -> str:
    """short lived token for Authorization.password never goes inside it."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return _encode(user_id, email, role, "access", expire)


def create_refresh_token(user_id: int, email: str, role: str) -> str:
    """longer token.only /auth/refresh accepts it."""
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    return _encode(user_id, email, role, "refresh", expire)


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise UnauthorizedException("Invalid or expired token")


def decode_access_token(token: str) -> dict:
    """a refresh token sent as bearer is rejected.bad signature is the same 401."""
    payload = _decode(token)
    if payload.get("type") != "access":
        raise UnauthorizedException("Access token is required")
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = _decode(token)
    if payload.get("type") != "refresh":
        raise UnauthorizedException("Refresh token is required")
    return payload
