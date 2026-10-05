"""checkout body and order response.client does not send total,server calculates it."""

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.utils import ALLOWED_PAYMENT_METHODS


class CheckoutRequest(BaseModel):
    user_id: int
    payment_method: str

    @field_validator("user_id")
    @classmethod
    def user_id_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("User id must be greater than 0")
        return value

    @field_validator("payment_method")
    @classmethod
    def payment_method_valid(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in ALLOWED_PAYMENT_METHODS:
            allowed = ", ".join(ALLOWED_PAYMENT_METHODS)
            raise ValueError(f"Payment method must be valid. Allowed values: {allowed}")
        return cleaned


class OrderLineResponse(BaseModel):
    order_detail_id: int
    product_id: int
    product_name: str
    quantity: int
    price: float
    line_total: float


class OrderHistoryItem(BaseModel):
    order_id: int
    order_number: str
    user_id: int
    order_date: datetime
    payment_method: str
    order_status: str
    payment_status: str
    payment_reference: str | None = None
    failure_reason: str | None = None
    total_amount: float


class OrderResponse(OrderHistoryItem):
    items: list[OrderLineResponse]


class CheckoutResponse(BaseModel):
    message: str
    order: OrderResponse


class PaymentProcessRequest(BaseModel):
    order_id: int

    @field_validator("order_id")
    @classmethod
    def order_id_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Order id must be greater than 0")
        return value


class NotifyRequest(PaymentProcessRequest):
    pass
