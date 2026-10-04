from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# OPEN is the basket of things not ordered yet. ORDERED means checkout already closed it.
CART_OPEN = "OPEN"
CART_ORDERED = "ORDERED"


class Cart(Base):
    """one shopping basket.cart_id starts at 1 for each user,not a global number."""

    __tablename__ = "Carts"
    __table_args__ = (
        CheckConstraint("\"Status\" IN ('OPEN', 'ORDERED')", name="ck_cart_status"),
        # a shopper only keeps one basket that is not ordered yet.
        Index("uq_user_one_open_cart", "UserID", unique=True, postgresql_where=text("\"Status\" = 'OPEN'")),
    )

    user_id: Mapped[int] = mapped_column(
        "UserID", Integer, ForeignKey("Users.UserID"), primary_key=True, autoincrement=False
    )
    cart_id: Mapped[int] = mapped_column("CartID", Integer, primary_key=True, autoincrement=False)
    status: Mapped[str] = mapped_column("Status", String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="carts")
    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", order_by="CartItem.product_id")


class CartItem(Base):
    """one product inside a cart.there is no separate cart item id."""

    __tablename__ = "CartItems"
    __table_args__ = (
        CheckConstraint('"Quantity" > 0', name="ck_cart_qty_positive"),
        ForeignKeyConstraint(
            ["UserID", "CartID"],
            ["Carts.UserID", "Carts.CartID"],
            name="fk_cartitem_cart",
        ),
    )

    user_id: Mapped[int] = mapped_column("UserID", Integer, primary_key=True, autoincrement=False)
    cart_id: Mapped[int] = mapped_column("CartID", Integer, primary_key=True, autoincrement=False)
    product_id: Mapped[int] = mapped_column(
        "ProductID", Integer, ForeignKey("Products.ProductID"), primary_key=True, autoincrement=False
    )
    quantity: Mapped[int] = mapped_column("Quantity", Integer, nullable=False)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")
