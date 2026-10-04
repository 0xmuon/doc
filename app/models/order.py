from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    """placed order.TotalAmount is the line sum."""

    __tablename__ = "Orders"
    __table_args__ = (
        CheckConstraint(
            "\"PaymentStatus\" IN ('PENDING', 'PAID', 'FAILED')",
            name="ck_order_payment_status",
        ),
    )

    order_id: Mapped[int] = mapped_column("OrderID", Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column("UserID", Integer, ForeignKey("Users.UserID"), nullable=False, index=True)
    order_date: Mapped[datetime] = mapped_column("OrderDate", DateTime, nullable=False)
    payment_method: Mapped[str] = mapped_column("PaymentMethod", String(30), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column("TotalAmount", Numeric(12, 2), nullable=False)
    # PENDING until the gateway answers.FAILED still keeps the order row.
    payment_status: Mapped[str] = mapped_column(
        "PaymentStatus", String(20), nullable=False, default="PENDING", server_default="PENDING"
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    details: Mapped[list["OrderDetail"]] = relationship(back_populates="order")


class OrderDetail(Base):
    """one bought line.Price is unit price copied from product at checkout."""

    __tablename__ = "OrderDetails"
    __table_args__ = (CheckConstraint('"Quantity" > 0', name="ck_order_qty_positive"),)

    order_detail_id: Mapped[int] = mapped_column("OrderDetailID", Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        "OrderID", Integer, ForeignKey("Orders.OrderID"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        "ProductID", Integer, ForeignKey("Products.ProductID"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column("Quantity", Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column("Price", Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="details")
    product: Mapped["Product"] = relationship(back_populates="order_details")
