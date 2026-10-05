"""checkout copies price on the order,reduces stock,and clears the cart lines in one commit."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.integrations import PAID, charge_order
from app.integrations.payment_gateway import PaymentOutcome
from app.models import Order, OrderDetail, Product
from app.repositories import audit_repository, cart_repository, order_repository, user_repository
from app.schemas import CheckoutRequest, CheckoutResponse, OrderHistoryItem, OrderLineResponse, OrderResponse
from app.utils import ALLOWED_PAYMENT_METHODS, AppException, NotFoundException, log_event, to_money, utcnow


def _history(order: Order) -> dict:
    return {
        "order_id": order.order_id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "order_date": order.created_at or order.order_date,
        "payment_method": order.payment_method,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "payment_reference": order.payment_reference,
        "failure_reason": order.failure_reason,
        "total_amount": float(to_money(order.total_amount)),
    }


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
    return OrderResponse(**_history(order), items=lines)


def _lock_stock(db: Session, items) -> None:
    """lock the product rows so two checkouts cant take the last unit."""
    ids = [item.product_id for item in items]
    locked = list(db.scalars(select(Product).where(Product.product_id.in_(ids)).with_for_update()).all())
    by_id = {row.product_id: row for row in locked}
    for item in items:
        item.product = by_id[item.product_id]


def _reserve(db: Session, payload: CheckoutRequest) -> tuple[int, str, str, str]:
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
            order_number=f"TMP-{uuid4().hex[:12]}",
            user_id=payload.user_id,
            order_date=utcnow(),
            payment_method=payload.payment_method,
            total_amount=total,
            order_status="PENDING_PAYMENT",
            payment_status="PENDING",
        ),
    )
    order.order_number = f"ORD-{order.order_id:06d}"
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
    order_number = order.order_number
    db.commit()
    return order_id, str(total), payload.payment_method, order_number


def _release_stock(order: Order) -> None:
    """a failed charge gives the reserved units back."""
    for line in order.details:
        line.product.available_quantity += line.quantity


def _write_outcome(db: Session, order: Order, outcome: PaymentOutcome) -> None:
    order.payment_status = outcome.status
    if outcome.status == PAID:
        order.order_status = "CONFIRMED"
        order.payment_reference = outcome.reference
        order.failure_reason = None
    else:
        order.order_status = "PAYMENT_FAILED"
        order.payment_reference = None
        order.failure_reason = (outcome.detail or "Payment failed")[:255]
        _release_stock(order)
    audit_repository.record(db, order.user_id, "payment", "order", order.order_id, order.payment_status)


def _apply_payment(db: Session, order_id: int, outcome: PaymentOutcome) -> CheckoutResponse:
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    _write_outcome(db, order, outcome)
    db.commit()
    log_event("payment_result", order_id=order_id, payment_status=outcome.status, detail=outcome.detail)
    saved = order_repository.get_by_id(db, order_id)
    message = "Order placed successfully" if outcome.status == PAID else "Order placed but payment failed"
    return CheckoutResponse(message=message, order=_to_order_response(saved))


async def checkout(db: AsyncSession, payload: CheckoutRequest) -> CheckoutResponse:
    """db work is run_sync so the driver can await.it does not block the loop on the charge."""
    order_id, total, method, number = await db.run_sync(lambda sync_db: _reserve(sync_db, payload))
    # charge is after the commit.a timeout must not roll the order back.
    outcome = await charge_order(order_id, total, method, number)
    return await db.run_sync(lambda sync_db: _apply_payment(sync_db, order_id, outcome))


def list_orders(db: Session, user_id: int) -> list[OrderHistoryItem]:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundException("User not found")
    orders = order_repository.list_by_user(db, user_id)
    return [
        OrderHistoryItem(**_history(order))
        for order in orders
    ]


def list_all_orders(db: Session) -> list[OrderHistoryItem]:
    orders = order_repository.list_all(db)
    return [OrderHistoryItem(**_history(order)) for order in orders]


def _load_for_retry(db: Session, order_id: int) -> tuple[str, str, str, str] | OrderResponse:
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    if order.payment_status == PAID:
        return _to_order_response(order)
    return str(order.total_amount), order.payment_method, order.payment_status, order.order_number


def _rehold(db: Session, order_id: int) -> None:
    """a failed order already gave the stock back,so a retry has to reserve it again."""
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    ids = [line.product_id for line in order.details]
    locked = list(db.scalars(select(Product).where(Product.product_id.in_(ids)).with_for_update()).all())
    by_id = {row.product_id: row for row in locked}
    for line in order.details:
        product = by_id[line.product_id]
        if line.quantity > product.available_quantity:
            raise AppException("Ordered quantity must not exceed available quantity")
        product.available_quantity -= line.quantity
    order.order_status = "PENDING_PAYMENT"
    order.payment_status = "PENDING"
    order.failure_reason = None
    db.commit()


def _store_retry(db: Session, order_id: int, outcome: PaymentOutcome) -> OrderResponse:
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    _write_outcome(db, order, outcome)
    db.commit()
    log_event("payment_retry", order_id=order_id, payment_status=outcome.status, detail=outcome.detail)
    saved = order_repository.get_by_id(db, order_id)
    return _to_order_response(saved)


async def retry_payment(db: AsyncSession, order_id: int) -> OrderResponse:
    """already PAID is left alone.so a second click does not charge again."""
    current = await db.run_sync(lambda sync_db: _load_for_retry(sync_db, order_id))
    if isinstance(current, OrderResponse):
        return current
    amount, method, status, number = current
    if status == "FAILED":
        await db.run_sync(lambda sync_db: _rehold(sync_db, order_id))
    outcome = await charge_order(order_id, amount, method, number)
    return await db.run_sync(lambda sync_db: _store_retry(sync_db, order_id, outcome))


def get_order(db: Session, order_id: int) -> OrderResponse:
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    return _to_order_response(order)
