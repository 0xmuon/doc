from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """shopper account.password is stored as an argon2 hash,not plain text."""

    __tablename__ = "Users"
    __table_args__ = (CheckConstraint("\"Role\" IN ('CUSTOMER', 'ADMIN', 'SUPPORT')", name="ck_user_role"),)

    user_id: Mapped[int] = mapped_column("UserID", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(100), nullable=False)
    email: Mapped[str] = mapped_column("Email", String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column("Password", String(255), nullable=False)
    mobile: Mapped[str] = mapped_column("Mobile", String(15), nullable=False)
    role: Mapped[str] = mapped_column("Role", String(20), nullable=False, default="CUSTOMER", server_default="CUSTOMER")
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, nullable=False, default=True, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column("UpdatedAt", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="user")
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
