"""admin writes for products and categories.reads stay on product_service."""

from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Category, Product, User
from app.repositories import audit_repository, product_repository
from app.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.services import product_service
from app.utils import ConflictException, NotFoundException


def _category_or_404(db: Session, category_id: int) -> Category:
    category = product_repository.get_category(db, category_id)
    if category is None:
        raise NotFoundException("Category not found")
    return category


def create_category(db: Session, payload: CategoryCreate, actor: User) -> CategoryResponse:
    if product_repository.get_category_by_name(db, payload.category_name):
        raise ConflictException("Category name must be unique")
    category = Category(category_name=payload.category_name)
    db.add(category)
    db.flush()
    audit_repository.record(db, actor.user_id, "create", "category", category.category_id, category.category_name)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException("Category name must be unique")
    db.refresh(category)
    return CategoryResponse.model_validate(category)


def update_category(db: Session, category_id: int, payload: CategoryUpdate, actor: User) -> CategoryResponse:
    category = _category_or_404(db, category_id)
    other = product_repository.get_category_by_name(db, payload.category_name)
    if other is not None and other.category_id != category.category_id:
        raise ConflictException("Category name must be unique")
    category.category_name = payload.category_name
    audit_repository.record(db, actor.user_id, "update", "category", category.category_id, category.category_name)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException("Category name must be unique")
    db.refresh(category)
    return CategoryResponse.model_validate(category)


def create_product(db: Session, payload: ProductCreate, actor: User) -> ProductResponse:
    _category_or_404(db, payload.category_id)
    if product_repository.get_by_name(db, payload.product_name):
        raise ConflictException("Product name must be unique")
    if product_repository.get_by_sku(db, payload.sku):
        raise ConflictException("SKU must be unique")
    product = Product(
        sku=payload.sku,
        product_name=payload.product_name,
        description=payload.description,
        category_id=payload.category_id,
        price=payload.price if isinstance(payload.price, Decimal) else Decimal(str(payload.price)),
        available_quantity=payload.available_quantity,
        product_url=payload.product_url,
        is_active=True,
    )
    db.add(product)
    db.flush()
    audit_repository.record(db, actor.user_id, "create", "product", product.product_id, product.sku)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException("Product name or SKU must be unique")
    saved = product_repository.get_by_id(db, product.product_id)
    return product_service.to_product_response(saved)


def update_product(db: Session, product_id: int, payload: ProductUpdate, actor: User) -> ProductResponse:
    product = product_repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundException("Product not found")
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data:
        _category_or_404(db, data["category_id"])
    if "product_name" in data:
        other = product_repository.get_by_name(db, data["product_name"])
        if other is not None and other.product_id != product.product_id:
            raise ConflictException("Product name must be unique")
    if "sku" in data:
        other_sku = product_repository.get_by_sku(db, data["sku"])
        if other_sku is not None and other_sku.product_id != product.product_id:
            raise ConflictException("SKU must be unique")
    for key, value in data.items():
        setattr(product, key, value)
    audit_repository.record(db, actor.user_id, "update", "product", product.product_id, product.sku)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException("Product name or SKU must be unique")
    saved = product_repository.get_by_id(db, product.product_id)
    return product_service.to_product_response(saved)


def deactivate_product(db: Session, product_id: int, actor: User) -> ProductResponse:
    """delete only turns the product off.the row stays so old orders still have a name."""
    product = product_repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundException("Product not found")
    product.is_active = False
    audit_repository.record(db, actor.user_id, "delete", "product", product.product_id, product.sku)
    db.commit()
    saved = product_repository.get_by_id(db, product.product_id)
    return product_service.to_product_response(saved)


def list_products_for_admin(db: Session) -> list[ProductResponse]:
    return [product_service.to_product_response(product) for product in product_repository.list_all(db, active_only=False)]
