from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """shopper account.password is stored as hash only,not plain text."""

    __tablename__ = "Users"

    user_id: Mapped[int] = mapped_column("UserID", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(100), nullable=False)
    email: Mapped[str] = mapped_column("Email", String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column("Password", String(255), nullable=False)
    mobile: Mapped[str] = mapped_column("Mobile", String(15), nullable=False)

    carts: Mapped[list["Cart"]] = relationship(back_populates="user")
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
