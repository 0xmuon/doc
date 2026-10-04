"""cart rules.same product added again increases Quantity on that CartItemID."""

from sqlalchemy.orm import Session

from app.models.cart import CartItem
from app.repositories import cart_repository, product_repository, user_repository
from app.schemas.cart_schema import (
    CartAddRequest,
    CartItemResponse,
    CartResponse,
    CartSummaryResponse,
    CartUpdateRequest,
)
from app.utils.exceptions import AppException, NotFoundException
from app.utils.helpers import to_money


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
        cart_item_id=item.cart_item_id,
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


def get_cart(db: Session, user_id: int) -> CartResponse:
    _require_user(db, user_id)
    items = cart_repository.list_for_user(db, user_id)
    return CartResponse(user_id=user_id, items=[_to_item_response(item) for item in items])


def get_summary(db: Session, user_id: int) -> CartSummaryResponse:
    cart = get_cart(db, user_id)
    total_quantity = sum(item.quantity for item in cart.items)
    total_amount = to_money(sum(item.line_total for item in cart.items))
    return CartSummaryResponse(
        user_id=user_id,
        distinct_items=len(cart.items),
        total_quantity=total_quantity,
        total_amount=float(total_amount),
        items=cart.items,
    )


def get_item(db: Session, cart_item_id: int, missing: str) -> CartItem:
    item = cart_repository.get_by_id(db, cart_item_id)
    if item is None:
        raise NotFoundException(missing)
    return item


def add_item(db: Session, payload: CartAddRequest, *, hide_inactive: bool = True) -> CartItemResponse:
    _require_user(db, payload.user_id)
    product = product_repository.get_by_id(db, payload.product_id)
    # is_active is missing on the earlier milestones,treat those products as active.
    inactive = hide_inactive and product is not None and not getattr(product, "is_active", True)
    if product is None or inactive:
        raise NotFoundException("Product must exist before adding to cart")

    existing = cart_repository.get_by_user_product(db, payload.user_id, payload.product_id)
    # same product added again keeps the same CartItemID and adds to Quantity.
    new_quantity = payload.quantity + (existing.quantity if existing else 0)
    _ensure_stock(new_quantity, product.available_quantity)
    if existing:
        existing.quantity = new_quantity
        saved_id = existing.cart_item_id
    else:
        row = CartItem(user_id=payload.user_id, product_id=payload.product_id, quantity=payload.quantity)
        db.add(row)
        db.flush()
        saved_id = row.cart_item_id
    db.commit()
    saved = cart_repository.get_by_id(db, saved_id)
    return _to_item_response(saved)


def update_item(db: Session, item: CartItem, payload: CartUpdateRequest) -> CartItemResponse:
    _ensure_stock(payload.quantity, item.product.available_quantity)
    item.quantity = payload.quantity
    cart_item_id = item.cart_item_id
    db.commit()
    saved = cart_repository.get_by_id(db, cart_item_id)
    return _to_item_response(saved)


def remove_item(db: Session, item: CartItem) -> None:
    db.delete(item)
    db.commit()
