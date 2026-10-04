"""checkout copies price on the order,reduces stock,and closes the open cart in one commit."""

from sqlalchemy.orm import Session

from app.models.cart import CART_ORDERED
from app.models.order import Order, OrderDetail
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


def _history(order: Order) -> OrderHistoryItem:
    return OrderHistoryItem(
        order_id=order.order_id,
        user_id=order.user_id,
        cart_id=order.cart_id,
        order_date=order.order_date,
        payment_method=order.payment_method,
        total_amount=float(to_money(order.total_amount)),
    )


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
    base = _history(order)
    return OrderResponse(**base.model_dump(), items=lines)


def checkout(db: Session, payload: CheckoutRequest) -> CheckoutResponse:
    if payload.payment_method not in ALLOWED_PAYMENT_METHODS:
        allowed = ", ".join(ALLOWED_PAYMENT_METHODS)
        raise AppException(f"Payment method must be valid. Allowed values: {allowed}")
    user = user_repository.get_by_id(db, payload.user_id)
    if user is None:
        raise NotFoundException("User not found")
    cart = cart_repository.get_open_cart(db, payload.user_id)
    if cart is None or not cart.items:
        raise AppException("User must have at least one cart item before checkout")

    total = to_money(0)
    for item in cart.items:
        # check stock again here,someone else may have bought it after it was in cart.
        if item.quantity > item.product.available_quantity:
            raise AppException("Ordered quantity must not exceed available quantity")
        total += to_money(to_money(item.product.price) * item.quantity)
    total = to_money(total)

    order = order_repository.create(
        db,
        Order(
            user_id=payload.user_id,
            cart_id=cart.cart_id,
            order_date=utcnow(),
            payment_method=payload.payment_method,
            total_amount=total,
        ),
    )
    for item in cart.items:
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
    # close this basket.the lines stay on it,but it is no longer the open cart.
    cart.status = CART_ORDERED
    # one commit so if it fails,stock,cart and order stay as they were.
    db.commit()
    saved = order_repository.get_by_id(db, order.order_id)
    return CheckoutResponse(message="Order placed successfully", order=_to_order_response(saved))


def list_orders(db: Session, user_id: int) -> list[OrderHistoryItem]:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundException("User not found")
    return [_history(order) for order in order_repository.list_by_user(db, user_id)]


def list_all_orders(db: Session) -> list[OrderHistoryItem]:
    return [_history(order) for order in order_repository.list_all(db)]


def get_order(db: Session, order_id: int) -> OrderResponse:
    order = order_repository.get_by_id(db, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    return _to_order_response(order)
