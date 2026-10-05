"""cart routes.update and remove use CartItemID,the caller must own that line."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas import (
    CartAddRequest,
    CartItemResponse,
    CartResponse,
    CartUpdateRequest,
    MessageResponse,
)
from app.services import cart_service
from app.utils import get_current_user, require_owner, require_permission

router = APIRouter(tags=["Cart"], dependencies=[Depends(get_current_user)])


@router.get("/cart/{user_id}", response_model=CartResponse, summary="Cart")
def view_cart(user_id: int, current: User = Depends(require_permission("cart:read")), db: Session = Depends(get_db)):
    require_owner(current, user_id, "cart")
    return cart_service.get_cart(db, user_id)


@router.post("/cart/add", response_model=CartItemResponse, status_code=201, summary="Add to cart")
def add_to_cart(
    payload: CartAddRequest,
    current: User = Depends(require_permission("cart:write")),
    db: Session = Depends(get_db),
):
    require_owner(current, payload.user_id, "cart")
    return cart_service.add_item(db, payload)


@router.put(
    "/cart/update/{cart_item_id}",
    response_model=CartItemResponse,
    summary="Update cart",
)
def update_cart_item(
    cart_item_id: int,
    payload: CartUpdateRequest,
    current: User = Depends(require_permission("cart:write")),
    db: Session = Depends(get_db),
):
    item = cart_service.get_item(db, cart_item_id, "Cart item must exist before update")
    require_owner(current, item.user_id, "cart")
    return cart_service.update_item(db, item, payload)


@router.delete(
    "/cart/remove/{cart_item_id}",
    response_model=MessageResponse,
    summary="Remove from cart",
)
def remove_cart_item(
    cart_item_id: int,
    current: User = Depends(require_permission("cart:write")),
    db: Session = Depends(get_db),
):
    item = cart_service.get_item(db, cart_item_id, "Cart item must exist before delete")
    require_owner(current, item.user_id, "cart")
    cart_service.remove_item(db, item)
    return MessageResponse(message="Item removed from cart")
