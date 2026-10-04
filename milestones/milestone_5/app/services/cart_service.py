"""cart rules.each user gets cart id 1 first,and the next basket after checkout is 2."""

from sqlalchemy.orm import Session

from app.models.cart import CART_OPEN, Cart, CartItem
from app.repositories import cart_repository, product_repository, user_repository
from app.schemas.cart_schema import (
    CartAddRequest,
    CartItemResponse,
    CartResponse,
    CartSummaryResponse,
    CartUpdateRequest,
)
from app.utils.exceptions import AppException, NotFoundException
from app.utils.helpers import to_money, utcnow


def _require_user(db: Session, user_id: int):
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundException("User not found")
    return user


def _to_item_response(item: CartItem) -> CartItemResponse:
    # cart uses current product price.order line copies that price later.
    unit_price = to_money(item.product.price)
    line_total = to_money(unit_price * item.quantity)
    return CartItemResponse(
        cart_id=item.cart_id,
        user_id=item.user_id,
        product_id=item.product_id,
        product_name=item.product.product_name,
        unit_price=float(unit_price),
        quantity=item.quantity,
        line_total=float(line_total),
        available_quantity=item.product.available_quantity,
    )


def _ensure_stock(quantity: int, available: int) -> None:
    if quantity > available:
        raise AppException("Quantity cannot exceed available stock")


def _bucket(cart: Cart | None, user_id: int) -> CartResponse:
    if cart is None:
        return CartResponse(user_id=user_id, cart_id=None, status=None, items=[])
    return CartResponse(
        user_id=user_id,
        cart_id=cart.cart_id,
        status=cart.status,
        items=[_to_item_response(item) for item in cart.items],
    )


def get_cart(db: Session, user_id: int) -> CartResponse:
    _require_user(db, user_id)
    return _bucket(cart_repository.get_open_cart(db, user_id), user_id)


def get_summary(db: Session, user_id: int) -> CartSummaryResponse:
    cart = get_cart(db, user_id)
    total_quantity = sum(item.quantity for item in cart.items)
    total_amount = to_money(sum(item.line_total for item in cart.items))
    return CartSummaryResponse(
        user_id=user_id,
        cart_id=cart.cart_id,
        distinct_items=len(cart.items),
        total_quantity=total_quantity,
        total_amount=float(total_amount),
        items=cart.items,
    )


def _open_line(db: Session, user_id: int, product_id: int) -> CartItem:
    _require_user(db, user_id)
    cart = cart_repository.get_open_cart(db, user_id)
    item = None
    if cart is not None:
        item = next((line for line in cart.items if line.product_id == product_id), None)
    if item is None:
        raise NotFoundException("Cart item must exist before update")
    return item


def add_item(db: Session, payload: CartAddRequest) -> CartItemResponse:
    _require_user(db, payload.user_id)
    product = product_repository.get_by_id(db, payload.product_id)
    if product is None or not product.is_active:
        raise NotFoundException("Product must exist before adding to cart")

    cart = cart_repository.get_open_cart(db, payload.user_id)
    if cart is None:
        # first add opens basket 1. after a checkout the next add opens 2,then 3.
        cart = Cart(
            user_id=payload.user_id,
            cart_id=cart_repository.next_cart_id(db, payload.user_id),
            status=CART_OPEN,
            created_at=utcnow(),
        )
        db.add(cart)
        db.flush()
        existing = None
    else:
        existing = next((line for line in cart.items if line.product_id == payload.product_id), None)

    # same product added again just updates the line inside this cart.
    new_quantity = payload.quantity + (existing.quantity if existing else 0)
    _ensure_stock(new_quantity, product.available_quantity)
    if existing:
        existing.quantity = new_quantity
    else:
        db.add(
            CartItem(
                user_id=payload.user_id,
                cart_id=cart.cart_id,
                product_id=payload.product_id,
                quantity=payload.quantity,
            )
        )
    db.commit()
    saved = cart_repository.get_line(db, payload.user_id, cart.cart_id, payload.product_id)
    return _to_item_response(saved)


def update_item(db: Session, user_id: int, product_id: int, payload: CartUpdateRequest) -> CartItemResponse:
    item = _open_line(db, user_id, product_id)
    _ensure_stock(payload.quantity, item.product.available_quantity)
    item.quantity = payload.quantity
    cart_id = item.cart_id
    db.commit()
    saved = cart_repository.get_line(db, user_id, cart_id, product_id)
    return _to_item_response(saved)


def remove_item(db: Session, user_id: int, product_id: int) -> None:
    _require_user(db, user_id)
    cart = cart_repository.get_open_cart(db, user_id)
    item = None
    if cart is not None:
        item = next((line for line in cart.items if line.product_id == product_id), None)
    if item is None:
        raise NotFoundException("Cart item must exist before delete")
    db.delete(item)
    db.commit()
