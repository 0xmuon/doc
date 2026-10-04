"""user rules.email has to be unique,password is hashed,and bad login gets one message only."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import user_repository
from app.schemas.user_schema import LoginResponse, RefreshRequest, RoleUpdate, UserCreate, UserLogin, UserResponse
from app.utils.exceptions import ConflictException, ForbiddenException, NotFoundException, UnauthorizedException
from app.utils.permissions import ADMIN
from app.utils.helpers import hash_password, verify_password
from app.utils.security import create_access_token, create_refresh_token, decode_refresh_token


def register_user(db: Session, payload: UserCreate) -> User:
    if user_repository.get_by_email(db, payload.email):
        raise ConflictException("Email must be unique")
    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        mobile=payload.mobile,
        role="CUSTOMER",
    )
    try:
        return user_repository.create(db, user)
    except IntegrityError:
        # if two people register same email together,still give unique email error.
        db.rollback()
        raise ConflictException("Email must be unique")


def login_user(db: Session, payload: UserLogin) -> LoginResponse:
    """find email in Users table and match password with the stored hash."""
    user = user_repository.get_by_email(db, payload.email)
    # same message if user is not there or password is wrong.
    if user is None or not verify_password(payload.password, user.password):
        raise UnauthorizedException("Invalid email or password")
    # token is issued only after the hash matches.cart and orders will ask for it.
    return _tokens(user)


def _tokens(user: User) -> LoginResponse:
    return LoginResponse(
        message="Login successful",
        access_token=create_access_token(user.user_id, user.email, user.role),
        refresh_token=create_refresh_token(user.user_id, user.email, user.role),
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


def refresh_session(db: Session, payload: RefreshRequest) -> LoginResponse:
    """swap a refresh token for a new pair.an access token is refused here."""
    data = decode_refresh_token(payload.refresh_token)
    try:
        user_id = int(data.get("sub"))
    except (TypeError, ValueError):
        raise UnauthorizedException("Invalid or expired token")
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise UnauthorizedException("Invalid or expired token")
    return _tokens(user)


def change_role(db: Session, actor: User, user_id: int, payload: RoleUpdate) -> User:
    """admin changes someone else.the last admin cannot be demoted."""
    if actor.user_id == user_id:
        raise ForbiddenException("You cannot change your own role")
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundException("User not found")
    if user.role == ADMIN and payload.role != ADMIN and user_repository.count_by_role(db, ADMIN) <= 1:
        raise ConflictException("At least one admin is required")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
