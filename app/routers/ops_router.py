"""payment retry and the notification trigger.both sit outside the checkout transaction."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db import get_async_db, get_db
from app.integrations import send_order_notification
from app.models import User
from app.policy import allow
from app.schemas import NotifyRequest, OrderResponse, PaymentProcessRequest
from app.services import order_service
from app.utils import ForbiddenException, get_current_user, has_permission, require_order_access

router = APIRouter(tags=["Operations"])


def _can_charge(current: User, owner_id: int) -> None:
    if allow(current.role, current.user_id, "payment", "process", owner_id):
        return
    if has_permission(current.role, "order:write"):
        raise ForbiddenException("You can only access your own orders")
    raise ForbiddenException("You do not have access to this action")


@router.post("/payments/process", response_model=OrderResponse, summary="Retry payment")
async def process_payment(
    payload: PaymentProcessRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    order = await db.run_sync(lambda sync_db: order_service.get_order(sync_db, payload.order_id))
    _can_charge(current, order.user_id)
    return await order_service.retry_payment(db, payload.order_id)


@router.post("/notifications/send", summary="Notify")
def send_notification(
    payload: NotifyRequest,
    background: BackgroundTasks,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = order_service.get_order(db, payload.order_id)
    require_order_access(current, order.user_id)
    background.add_task(send_order_notification, order.order_id, current.email, order.payment_status)
    return {"message": "Notification queued", "order_id": order.order_id}
