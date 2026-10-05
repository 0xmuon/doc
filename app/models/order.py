from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    """placed order.order status and payment status are saved together."""

    __tablename__ = "Orders"
    __table_args__ = (
        CheckConstraint(
            "\"PaymentStatus\" IN ('PENDING', 'PAID', 'FAILED')",
            name="ck_order_payment_status",
        ),
        CheckConstraint(
            "\"OrderStatus\" IN ('PENDING_PAYMENT', 'CONFIRMED', 'PAYMENT_FAILED')",
            name="ck_order_status",
        ),
    )

    order_id: Mapped[int] = mapped_column("OrderID", Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column("OrderNumber", String(20), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column("UserID", Integer, ForeignKey("Users.UserID"), nullable=False, index=True)
    order_date: Mapped[datetime] = mapped_column("OrderDate", DateTime, nullable=False)
    payment_method: Mapped[str] = mapped_column("PaymentMethod", String(30), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column("TotalAmount", Numeric(12, 2), nullable=False)
    order_status: Mapped[str] = mapped_column(
        "OrderStatus", String(20), nullable=False, default="PENDING_PAYMENT", server_default="PENDING_PAYMENT"
    )
    payment_status: Mapped[str] = mapped_column(
        "PaymentStatus", String(20), nullable=False, default="PENDING", server_default="PENDING"
    )
    payment_reference: Mapped[str | None] = mapped_column("PaymentReference", String(40))
    failure_reason: Mapped[str | None] = mapped_column("FailureReason", String(255))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column("UpdatedAt", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="orders")
    details: Mapped[list["OrderDetail"]] = relationship(back_populates="order")


class OrderDetail(Base):
    """one bought line.price is the unit price copied from the product at checkout."""

    __tablename__ = "OrderDetails"
    __table_args__ = (CheckConstraint('"Quantity" > 0', name="ck_order_qty_positive"),)

    order_detail_id: Mapped[int] = mapped_column("OrderDetailID", Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column("OrderID", Integer, ForeignKey("Orders.OrderID"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(
        "ProductID", Integer, ForeignKey("Products.ProductID"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column("Quantity", Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column("Price", Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="details")
    product: Mapped["Product"] = relationship(back_populates="order_details")
