"""order routes.caller is taken from the token,not trusted from the path alone."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.order_schema import CheckoutRequest, CheckoutResponse, OrderHistoryItem, OrderResponse
from app.services import order_service
from app.utils.deps import get_current_user, require_owner
from app.utils.exceptions import ForbiddenException

router = APIRouter(tags=["Orders"], dependencies=[Depends(get_current_user)])


@router.post("/orders/checkout", response_model=CheckoutResponse, status_code=201, summary="Place an order")
def checkout(
    payload: CheckoutRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_owner(current, payload.user_id, "orders")
    return order_service.checkout(db, payload)


@router.get("/orders/details/{order_id}", response_model=OrderResponse, summary="View order details")
def order_details(order_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id)
    if order.user_id != current.user_id:
        raise ForbiddenException("You can only access your own orders")
    return order


@router.get("/orders/me", response_model=list[OrderHistoryItem], summary="View my order history")
def my_orders(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return order_service.list_orders(db, current.user_id)


@router.get("/orders/{user_id}", response_model=list[OrderHistoryItem], summary="View order history")
def order_history(user_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_owner(current, user_id, "orders")
    return order_service.list_orders(db, user_id)
