"""payment retry.the order row is already saved before this runs."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.order_schema import OrderResponse, PaymentProcessRequest
from app.services import order_service
from app.utils.deps import get_current_user
from app.utils.exceptions import ForbiddenException
from app.utils.permissions import has_permission

router = APIRouter(tags=["Operations"])


def _can_charge(current: User, owner_id: int) -> None:
    if has_permission(current.role, "catalog:manage"):
        return
    if has_permission(current.role, "order:write") and current.user_id == owner_id:
        return
    if has_permission(current.role, "order:write"):
        raise ForbiddenException("You can only access your own orders")
    raise ForbiddenException("You do not have access to this action")


@router.post("/payments/process", response_model=OrderResponse, summary="Retry payment for an order")
def process_payment(
    payload: PaymentProcessRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = order_service.get_order(db, payload.order_id)
    _can_charge(current, order.user_id)
    return order_service.retry_payment(db, payload.order_id)
