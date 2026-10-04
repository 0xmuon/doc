from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CartItem(Base):
    """one line in the shopper cart.CartItemID is the id from week 2,auto generated."""

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

    user: Mapped["User"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")
