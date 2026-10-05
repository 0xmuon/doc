"""user table work.this file does its own commit."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def count_by_role(db: Session, role: str) -> int:
    count = db.scalar(select(func.count()).select_from(User).where(User.role == role))
    return int(count or 0)


def create(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
