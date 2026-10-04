from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Product(Base):
    """one product.CategoryID points at Categories.AvailableQuantity is current stock."""

    __tablename__ = "Products"

    product_id: Mapped[int] = mapped_column("ProductID", Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column("ProductName", String(200), unique=True, nullable=False)
    description: Mapped[str] = mapped_column("Description", Text, nullable=False)
    category_id: Mapped[int] = mapped_column(
        "CategoryID", Integer, ForeignKey("Categories.CategoryID"), nullable=False, index=True
    )
    price: Mapped[Decimal] = mapped_column("Price", Numeric(10, 2), nullable=False)
    available_quantity: Mapped[int] = mapped_column("AvailableQuantity", Integer, nullable=False)
    product_url: Mapped[str] = mapped_column("ProductUrl", String(500), nullable=False)

    category: Mapped["Category"] = relationship(back_populates="products")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="product")
    order_details: Mapped[list["OrderDetail"]] = relationship(back_populates="product")
