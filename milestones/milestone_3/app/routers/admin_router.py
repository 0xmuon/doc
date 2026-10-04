"""admin routes.permission is checked here,shop rules stay in the service."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.order_schema import OrderHistoryItem
from app.schemas.product_schema import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.schemas.user_schema import RoleUpdate, UserResponse
from app.services import admin_service, order_service, user_service
from app.utils.deps import require_permission

router = APIRouter(tags=["Admin"])


@router.post("/admin/categories", response_model=CategoryResponse, status_code=201, summary="Create a category")
def create_category(
    payload: CategoryCreate,
    _: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.create_category(db, payload)


@router.put("/admin/categories/{category_id}", response_model=CategoryResponse, summary="Update a category")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    _: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.update_category(db, category_id, payload)


@router.get("/admin/products", response_model=list[ProductResponse], summary="List products including inactive")
def list_products(
    _: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.list_products_for_admin(db)


@router.post("/admin/products", response_model=ProductResponse, status_code=201, summary="Create a product")
def create_product(
    payload: ProductCreate,
    _: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.create_product(db, payload)


@router.put("/admin/products/{product_id}", response_model=ProductResponse, summary="Update or deactivate a product")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    _: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.update_product(db, product_id, payload)


@router.get("/admin/orders", response_model=list[OrderHistoryItem], summary="View every order")
def list_orders(
    _: User = Depends(require_permission("order:read:any")),
    db: Session = Depends(get_db),
):
    return order_service.list_all_orders(db)


@router.patch("/admin/users/{user_id}/role", response_model=UserResponse, summary="Change a user's role")
def change_role(
    user_id: int,
    payload: RoleUpdate,
    current: User = Depends(require_permission("user:role")),
    db: Session = Depends(get_db),
):
    user = user_service.change_role(db, current, user_id, payload)
    return UserResponse.model_validate(user)
