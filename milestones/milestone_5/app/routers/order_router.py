"""order routes.caller is taken from the token,not trusted from the path alone."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.notification import send_order_notification
from app.models.user import User
from app.schemas.order_schema import CheckoutRequest, CheckoutResponse, OrderHistoryItem, OrderResponse
from app.services import order_service
from app.utils.deps import get_current_user, require_order_access, require_owner, require_permission

router = APIRouter(tags=["Orders"], dependencies=[Depends(get_current_user)])


@router.post("/orders/checkout", response_model=CheckoutResponse, status_code=201, summary="Place an order")
def checkout(
    payload: CheckoutRequest,
    background: BackgroundTasks,
    current: User = Depends(require_permission("order:write")),
    db: Session = Depends(get_db),
):
    require_owner(current, payload.user_id, "orders")
    result = order_service.checkout(db, payload)
    # notice runs after the response.a slow email must not hold checkout.
    background.add_task(
        send_order_notification,
        result.order.order_id,
        current.email,
        result.order.payment_status,
    )
    return result


@router.get("/orders/details/{order_id}", response_model=OrderResponse, summary="View order details")
def order_details(order_id: int, current: User = Depends(require_permission("order:read:own")), db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id)
    require_order_access(current, order.user_id)
    return order


@router.get("/orders/me", response_model=list[OrderHistoryItem], summary="View my order history")
def my_orders(current: User = Depends(require_permission("order:read:own")), db: Session = Depends(get_db)):
    return order_service.list_orders(db, current.user_id)


@router.get("/orders/{user_id}", response_model=list[OrderHistoryItem], summary="View order history")
def order_history(user_id: int, current: User = Depends(require_permission("order:read:own")), db: Session = Depends(get_db)):
    require_order_access(current, user_id)
    return order_service.list_orders(db, user_id)
