from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CartItem(Base):
    """one line per user and product.adding the same product again raises the quantity."""

    __tablename__ = "CartItems"
    __table_args__ = (
        CheckConstraint('"Quantity" > 0', name="ck_cart_qty_positive"),
        UniqueConstraint("UserID", "ProductID", name="uq_user_product_cart"),
    )

    cart_item_id: Mapped[int] = mapped_column("CartItemID", Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column("UserID", Integer, ForeignKey("Users.UserID"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(
        "ProductID", Integer, ForeignKey("Products.ProductID"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column("Quantity", Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column("UpdatedAt", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")
