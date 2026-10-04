"""cart table work.open cart is the basket that is not ordered yet."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.cart import CART_OPEN, Cart, CartItem


def _open_cart_query():
    return select(Cart).options(joinedload(Cart.items).joinedload(CartItem.product))


def get_open_cart(db: Session, user_id: int) -> Cart | None:
    statement = _open_cart_query().where(Cart.user_id == user_id, Cart.status == CART_OPEN)
    return db.scalars(statement).unique().one_or_none()


def next_cart_id(db: Session, user_id: int) -> int:
    # first basket for this user is 1,even if some other user already has carts.
    current = db.scalar(select(func.max(Cart.cart_id)).where(Cart.user_id == user_id))
    return int(current or 0) + 1


def get_line(db: Session, user_id: int, cart_id: int, product_id: int) -> CartItem | None:
    statement = (
        select(CartItem)
        .options(joinedload(CartItem.product))
        .where(
            CartItem.user_id == user_id,
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
    )
    return db.scalar(statement)
