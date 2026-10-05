"""order routes.caller is taken from the token,not trusted from the path alone."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db import get_async_db, get_db
from app.integrations import send_order_notification
from app.models import User
from app.schemas import CheckoutRequest, CheckoutResponse, OrderHistoryItem, OrderResponse
from app.services import order_service
from app.utils import get_current_user, require_order_access, require_owner, require_permission

router = APIRouter(tags=["Orders"], dependencies=[Depends(get_current_user)])


@router.post("/orders/checkout", response_model=CheckoutResponse, status_code=201, summary="Checkout")
async def checkout(
    payload: CheckoutRequest,
    background: BackgroundTasks,
    current: User = Depends(require_permission("order:write")),
    db: AsyncSession = Depends(get_async_db),
):
    require_owner(current, payload.user_id, "orders")
    result = await order_service.checkout(db, payload)
    # notice runs after the response.a slow email must not hold checkout.
    background.add_task(
        send_order_notification,
        result.order.order_id,
        current.email,
        result.order.payment_status,
    )
    return result


@router.get("/orders/details/{order_id}", response_model=OrderResponse, summary="Order")
def order_details(order_id: int, current: User = Depends(require_permission("order:read:own")), db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id)
    require_order_access(current, order.user_id)
    return order


@router.get("/orders/me", response_model=list[OrderHistoryItem], summary="My orders")
def my_orders(current: User = Depends(require_permission("order:read:own")), db: Session = Depends(get_db)):
    return order_service.list_orders(db, current.user_id)
