from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Product(Base):
    """one product.sku is unique.price is above zero and stock cannot go negative."""

    __tablename__ = "Products"
    __table_args__ = (
        CheckConstraint('"Price" > 0', name="ck_products_price_positive"),
        CheckConstraint('"AvailableQuantity" >= 0', name="ck_products_stock_not_negative"),
    )

    product_id: Mapped[int] = mapped_column("ProductID", Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column("SKU", String(30), unique=True, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column("ProductName", String(200), unique=True, nullable=False)
    description: Mapped[str] = mapped_column("Description", Text, nullable=False)
    category_id: Mapped[int] = mapped_column(
        "CategoryID", Integer, ForeignKey("Categories.CategoryID"), nullable=False, index=True
    )
    price: Mapped[Decimal] = mapped_column("Price", Numeric(10, 2), nullable=False)
    available_quantity: Mapped[int] = mapped_column("AvailableQuantity", Integer, nullable=False)
    product_url: Mapped[str] = mapped_column("ProductUrl", String(500), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, nullable=False, default=True, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column("UpdatedAt", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category: Mapped["Category"] = relationship(back_populates="products")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="product")
    order_details: Mapped[list["OrderDetail"]] = relationship(back_populates="product")
