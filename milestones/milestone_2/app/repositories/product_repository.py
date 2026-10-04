"""product queries.category is loaded with product so we dont query again per row."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.product import Product


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.category_id)).all())


def _base_query():
    return select(Product).options(joinedload(Product.category)).order_by(Product.product_id)


def list_all(db: Session) -> list[Product]:
    return list(db.scalars(_base_query()).unique().all())


def get_by_id(db: Session, product_id: int) -> Product | None:
    statement = _base_query().where(Product.product_id == product_id)
    return db.scalar(statement)


def search(db: Session, name: str | None, category: str | None) -> list[Product]:
    statement = _base_query()
    if name:
        statement = statement.where(Product.product_name.ilike(f"%{name.strip()}%"))
    if category:
        cleaned = category.strip()
        # if number then filter by CategoryID.else match CategoryName,ignore case.
        if cleaned.isdigit():
            statement = statement.where(Product.category_id == int(cleaned))
        else:
            statement = statement.join(Product.category).where(func.lower(Category.category_name) == cleaned.lower())
    return list(db.scalars(statement).unique().all())
