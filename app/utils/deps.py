"""route protection.cart and orders need a bearer token,browse stays open."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.policy import allow
from app.repositories import user_repository
from app.utils import ForbiddenException, UnauthorizedException, decode_access_token, has_permission

# auto_error false so a missing header is our 401,not fastapi's default 403.
# scheme name JWT is the second box in swagger authorize.login is added beside it.
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="JWT")


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
    if user is None or not user.is_active:
        raise UnauthorizedException("Invalid or expired token")
    return user


def require_owner(current_user: User, user_id: int, what: str) -> None:
    """casbin own-rule.the token user and the row user have to be the same person."""
    resource = "cart" if what == "cart" else "order"
    if allow(current_user.role, current_user.user_id, resource, "own", user_id):
        return
    raise ForbiddenException(f"You can only access your own {what}")


def require_permission(permission: str):
    """reusable gate.the permission name is the only thing a route should pass."""

    def checker(current: User = Depends(get_current_user)) -> User:
        if not has_permission(current.role, permission):
            raise ForbiddenException("You do not have access to this action")
        return current

    return checker


def require_order_access(current_user: User, user_id: int) -> None:
    """admin and support can open any order.a customer only opens their own."""
    if allow(current_user.role, current_user.user_id, "order", "read", user_id):
        return
    if has_permission(current_user.role, "order:read:own"):
        raise ForbiddenException("You can only access your own orders")
    raise ForbiddenException("You do not have access to this action")
