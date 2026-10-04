"""user rules.email has to be unique,password is hashed,and bad login gets one message only."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import user_repository
from app.schemas.user_schema import LoginResponse, UserCreate, UserLogin, UserResponse
from app.utils.exceptions import ConflictException, UnauthorizedException
from app.utils.helpers import hash_password, verify_password
from app.utils.security import create_access_token


def register_user(db: Session, payload: UserCreate) -> User:
    if user_repository.get_by_email(db, payload.email):
        raise ConflictException("Email must be unique")
    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        mobile=payload.mobile,
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
    token = create_access_token(user.user_id, user.email)
    return LoginResponse(
        message="Login successful",
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
