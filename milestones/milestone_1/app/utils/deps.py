"""route protection.cart and orders need a bearer token,browse stays open."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories import user_repository
from app.utils.exceptions import ForbiddenException, UnauthorizedException
from app.utils.security import decode_access_token

# auto_error false so a missing header is our 401,not fastapi's default 403.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """read user id from the token,then load that row from Users."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("Valid token is required")
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise UnauthorizedException("Invalid or expired token")
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise UnauthorizedException("Invalid or expired token")
    return user


def require_owner(current_user: User, user_id: int, what: str) -> None:
    """token user and the id in the path or body have to be the same person."""
    if current_user.user_id != user_id:
        raise ForbiddenException(f"You can only access your own {what}")
