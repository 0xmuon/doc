"""admin routes.permission is checked here,shop rules stay in the service."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas import (
    AuditLogResponse,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    OrderHistoryItem,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    RoleUpdate,
    UserResponse,
)
from app.services import admin_service, order_service, user_service
from app.utils import require_permission

router = APIRouter(tags=["Admin"])


@router.post("/admin/categories", response_model=CategoryResponse, status_code=201, summary="Create category")
def create_category(
    payload: CategoryCreate,
    current: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.create_category(db, payload, current)


@router.put("/admin/categories/{category_id}", response_model=CategoryResponse, summary="Update category")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    current: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.update_category(db, category_id, payload, current)


@router.get("/admin/products", response_model=list[ProductResponse], summary="Products")
def list_products(
    _: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.list_products_for_admin(db)


@router.post("/admin/products", response_model=ProductResponse, status_code=201, summary="Create product")
def create_product(
    payload: ProductCreate,
    current: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.create_product(db, payload, current)


@router.put("/admin/products/{product_id}", response_model=ProductResponse, summary="Update product")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.update_product(db, product_id, payload, current)


@router.delete("/admin/products/{product_id}", response_model=ProductResponse, summary="Delete product")
def delete_product(
    product_id: int,
    current: User = Depends(require_permission("catalog:manage")),
    db: Session = Depends(get_db),
):
    return admin_service.deactivate_product(db, product_id, current)


@router.get("/admin/audit-logs", response_model=list[AuditLogResponse], summary="Audit logs")
def audit_logs(
    _: User = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db),
):
    from app.repositories import audit_repository

    return [AuditLogResponse.model_validate(row) for row in audit_repository.list_recent(db)]


@router.get("/admin/orders", response_model=list[OrderHistoryItem], summary="Orders")
def list_orders(
    _: User = Depends(require_permission("order:read:any")),
    db: Session = Depends(get_db),
):
    return order_service.list_all_orders(db)


@router.patch("/admin/users/{user_id}/role", response_model=UserResponse, summary="Change role")
def change_role(
    user_id: int,
    payload: RoleUpdate,
    current: User = Depends(require_permission("user:role")),
    db: Session = Depends(get_db),
):
    user = user_service.change_role(db, current, user_id, payload)
    return UserResponse.model_validate(user)
