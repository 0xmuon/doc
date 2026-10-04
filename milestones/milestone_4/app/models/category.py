from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Category(Base):
    """product grouping.CategoryName has to be unique."""

    __tablename__ = "Categories"

    category_id: Mapped[int] = mapped_column("CategoryID", Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column("CategoryName", String(100), unique=True, nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="category")
