"""cart lines.one row per user and product,found by CartItemID."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import CartItem


def _with_product():
    return select(CartItem).options(joinedload(CartItem.product)).order_by(CartItem.cart_item_id)


def list_for_user(db: Session, user_id: int) -> list[CartItem]:
    statement = _with_product().where(CartItem.user_id == user_id)
    return list(db.scalars(statement).unique().all())


def get_by_id(db: Session, cart_item_id: int) -> CartItem | None:
    statement = _with_product().where(CartItem.cart_item_id == cart_item_id)
    return db.scalar(statement)


def get_by_user_product(db: Session, user_id: int, product_id: int) -> CartItem | None:
    statement = _with_product().where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    return db.scalar(statement)
