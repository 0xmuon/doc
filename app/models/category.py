from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Category(Base):
    """product grouping.category name has to be unique."""

    __tablename__ = "Categories"

    category_id: Mapped[int] = mapped_column("CategoryID", Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column("CategoryName", String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column("UpdatedAt", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    products: Mapped[list["Product"]] = relationship(back_populates="category")
