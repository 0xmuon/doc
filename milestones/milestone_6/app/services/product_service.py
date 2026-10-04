"""product read side.price comes back with 2 decimal places."""

from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories import product_repository
from app.schemas.product_schema import CategoryResponse, ProductResponse
from app.utils.exceptions import NotFoundException
from app.utils.helpers import to_money


def to_product_response(product: Product) -> ProductResponse:
    return ProductResponse(
        product_id=product.product_id,
        product_name=product.product_name,
        description=product.description,
        category_id=product.category_id,
        category_name=product.category.category_name,
        price=float(to_money(product.price)),
        available_quantity=product.available_quantity,
        product_url=product.product_url,
        is_active=product.is_active,
    )


def list_categories(db: Session) -> list[CategoryResponse]:
    return [CategoryResponse.model_validate(category) for category in product_repository.list_categories(db)]


async def list_categories_async(db) -> list[CategoryResponse]:
    rows = await product_repository.list_categories_async(db)
    return [CategoryResponse.model_validate(category) for category in rows]


def list_products(db: Session) -> list[ProductResponse]:
    return [to_product_response(product) for product in product_repository.list_all(db)]


def get_product(db: Session, product_id: int) -> ProductResponse:
    product = product_repository.get_by_id(db, product_id)
    if product is None or not product.is_active:
        raise NotFoundException("Product not found")
    return to_product_response(product)


def search_products(db: Session, name: str | None, category: str | None) -> list[ProductResponse]:
    return [to_product_response(product) for product in product_repository.search(db, name, category)]
