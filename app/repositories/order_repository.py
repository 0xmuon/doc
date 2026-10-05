"""order table work.create() only flush so checkout can add lines before one commit."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Order, OrderDetail


def _with_details():
    return select(Order).options(joinedload(Order.details).joinedload(OrderDetail.product))


def create(db: Session, order: Order) -> Order:
    db.add(order)
    db.flush()
    return order


def list_by_user(db: Session, user_id: int) -> list[Order]:
    statement = _with_details().where(Order.user_id == user_id).order_by(Order.created_at.desc(), Order.order_id.desc())
    return list(db.scalars(statement).unique().all())


def list_all(db: Session) -> list[Order]:
    statement = _with_details().order_by(Order.created_at.desc(), Order.order_id.desc())
    return list(db.scalars(statement).unique().all())


def get_by_id(db: Session, order_id: int) -> Order | None:
    statement = _with_details().where(Order.order_id == order_id)
    return db.scalar(statement)
