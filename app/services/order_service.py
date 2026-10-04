"""checkout copies price on the order,reduces stock,and clears the cart lines in one commit."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.integrations.payment_gateway import PAID, charge_order
from app.models.order import Order, OrderDetail
from app.models.product import Product
from app.utils.logging_setup import log_event
from app.repositories import cart_repository, order_repository, user_repository
from app.schemas.order_schema import (
    CheckoutRequest,
    CheckoutResponse,
    OrderHistoryItem,
    OrderLineResponse,
    OrderResponse,
)
from app.utils.exceptions import AppException, NotFoundException
from app.utils.helpers import ALLOWED_PAYMENT_METHODS, to_money, utcnow


def _to_order_response(order: Order) -> OrderResponse:
    lines: list[OrderLineResponse] = []
    for detail in order.details:
        unit_price = to_money(detail.price)
        line_total = to_money(unit_price * detail.quantity)
        lines.append(
            OrderLineResponse(
                order_detail_id=detail.order_detail_id,
                product_id=detail.product_id,
                product_name=detail.product.product_name,
                quantity=detail.quantity,
                price=float(unit_price),
                line_total=float(line_total),
            )
        )
    return OrderResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        order_date=order.order_date,
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        total_amount=float(to_money(order.total_amount)),
        items=lines,
    )


def _lock_stock(db: Session, items) -> None:
    """on postgres the product rows are locked so two checkouts cant take the last unit."""
    bind = db.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return
    ids = [item.product_id for item in items]
    locked = list(db.scalars(select(Product).where(Product.product_id.in_(ids)).with_for_update()).all())
    by_id = {row.product_id: row for row in locked}
    for item in items:
        item.product = by_id[item.product_id]


def _reserve(db: Session, payload: CheckoutRequest) -> tuple[int, str, str]:
    if payload.payment_method not in ALLOWED_PAYMENT_METHODS:
        allowed = ", ".join(ALLOWED_PAYMENT_METHODS)
        raise AppException(f"Payment method must be valid. Allowed values: {allowed}")
    user = user_repository.get_by_id(db, payload.user_id)
    if user is None:
        raise NotFoundException("User not found")
    items = cart_repository.list_for_user(db, payload.user_id)
    if not items:
        raise AppException("User must have at least one cart item before checkout")
    _lock_stock(db, items)

    total = to_money(0)
    for item in items:
        # check stock again here,someone else may have bought it after it was in cart.
        if item.quantity > item.product.available_quantity:
            raise AppException("Ordered quantity must not exceed available quantity")
        total += to_money(to_money(item.product.price) * item.quantity)
    total = to_money(total)

    order = order_repository.create(
        db,
        Order(
            user_id=payload.user_id,
            order_date=utcnow(),
            payment_method=payload.payment_method,
            total_amount=total,
            payment_status="PENDING",
        ),
    )
    for item in items:
        unit_price = to_money(item.product.price)
        db.add(
            OrderDetail(
                order_id=order.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=unit_price,
            )
        )
        item.product.available_quantity -= item.quantity
    # week 2 cart is the lines.checkout removes them after the order is built.
    for item in items:
        db.delete(item)
    # one commit so if it fails,stock,cart and order stay as they were.
    order_id = order.order_id
    db.commit()
    return order_id, str(total), payload.payment_method


def _apply_payment(db: Session, order_id: int, status: str, detail: str) -> CheckoutResponse:
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    order.payment_status = status
    db.commit()
    log_event("payment_result", order_id=order_id, payment_status=status, detail=detail)
    saved = order_repository.get_by_id(db, order_id)
    message = "Order placed successfully" if status == PAID else "Order placed but payment failed"
    return CheckoutResponse(message=message, order=_to_order_response(saved))


async def checkout(db: AsyncSession, payload: CheckoutRequest) -> CheckoutResponse:
    """db work is run_sync so the driver can await.it does not block the loop on the gateway."""
    order_id, total, method = await db.run_sync(lambda sync_db: _reserve(sync_db, payload))
    # gateway is after the commit.a timeout must not roll the order back.
    outcome = await charge_order(order_id, total, method)
    return await db.run_sync(lambda sync_db: _apply_payment(sync_db, order_id, outcome.status, outcome.detail))


def list_orders(db: Session, user_id: int) -> list[OrderHistoryItem]:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundException("User not found")
    orders = order_repository.list_by_user(db, user_id)
    return [
        OrderHistoryItem(
            order_id=order.order_id,
            user_id=order.user_id,
            order_date=order.order_date,
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            total_amount=float(to_money(order.total_amount)),
        )
        for order in orders
    ]


def list_all_orders(db: Session) -> list[OrderHistoryItem]:
    orders = order_repository.list_all(db)
    return [
        OrderHistoryItem(
            order_id=order.order_id,
            user_id=order.user_id,
            order_date=order.order_date,
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            total_amount=float(to_money(order.total_amount)),
        )
        for order in orders
    ]


def _load_for_retry(db: Session, order_id: int) -> tuple[str, str, str] | OrderResponse:
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    if order.payment_status == PAID:
        return _to_order_response(order)
    return str(order.total_amount), order.payment_method, order.payment_status


def _store_retry(db: Session, order_id: int, status: str, detail: str) -> OrderResponse:
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    order.payment_status = status
    db.commit()
    log_event("payment_retry", order_id=order_id, payment_status=status, detail=detail)
    saved = order_repository.get_by_id(db, order_id)
    return _to_order_response(saved)


async def retry_payment(db: AsyncSession, order_id: int) -> OrderResponse:
    """already PAID is left alone.so a second click does not charge again."""
    current = await db.run_sync(lambda sync_db: _load_for_retry(sync_db, order_id))
    if isinstance(current, OrderResponse):
        return current
    amount, method, _status = current
    outcome = await charge_order(order_id, amount, method)
    return await db.run_sync(lambda sync_db: _store_retry(sync_db, order_id, outcome.status, outcome.detail))


def get_order(db: Session, order_id: int) -> OrderResponse:
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    return _to_order_response(order)
