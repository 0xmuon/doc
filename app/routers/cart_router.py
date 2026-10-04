"""cart routes.lines are found by user and product,and the caller must be that user."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.cart_schema import (
    CartAddRequest,
    CartItemResponse,
    CartResponse,
    CartSummaryResponse,
    CartUpdateRequest,
    MessageResponse,
)
from app.services import cart_service
from app.utils.deps import get_current_user, require_owner, require_permission

router = APIRouter(tags=["Cart"], dependencies=[Depends(get_current_user)])


@router.get("/cart/{user_id}/summary", response_model=CartSummaryResponse, summary="View cart summary")
def cart_summary(user_id: int, current: User = Depends(require_permission("cart:read")), db: Session = Depends(get_db)):
    require_owner(current, user_id, "cart")
    return cart_service.get_summary(db, user_id)


@router.get("/cart/{user_id}", response_model=CartResponse, summary="View user cart")
def view_cart(user_id: int, current: User = Depends(require_permission("cart:read")), db: Session = Depends(get_db)):
    require_owner(current, user_id, "cart")
    return cart_service.get_cart(db, user_id)


@router.post("/cart/add", response_model=CartItemResponse, status_code=201, summary="Add item to cart")
def add_to_cart(
    payload: CartAddRequest,
    current: User = Depends(require_permission("cart:write")),
    db: Session = Depends(get_db),
):
    require_owner(current, payload.user_id, "cart")
    return cart_service.add_item(db, payload)


@router.put(
    "/cart/update/{user_id}/{product_id}",
    response_model=CartItemResponse,
    summary="Update cart item quantity",
)
def update_cart_item(
    user_id: int,
    product_id: int,
    payload: CartUpdateRequest,
    current: User = Depends(require_permission("cart:write")),
    db: Session = Depends(get_db),
):
    require_owner(current, user_id, "cart")
    return cart_service.update_item(db, user_id, product_id, payload)


@router.delete(
    "/cart/remove/{user_id}/{product_id}",
    response_model=MessageResponse,
    summary="Remove item from cart",
)
def remove_cart_item(
    user_id: int,
    product_id: int,
    current: User = Depends(require_permission("cart:write")),
    db: Session = Depends(get_db),
):
    require_owner(current, user_id, "cart")
    cart_service.remove_item(db, user_id, product_id)
    return MessageResponse(message="Item removed from cart")
