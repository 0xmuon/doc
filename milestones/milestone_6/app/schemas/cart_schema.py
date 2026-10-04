"""cart body.quantity must be greater then 0,stock is checked in service."""

from pydantic import BaseModel, Field


class CartAddRequest(BaseModel):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class CartUpdateRequest(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    cart_item_id: int
    user_id: int
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    line_total: float
    available_quantity: int


class CartResponse(BaseModel):
    user_id: int
    items: list[CartItemResponse]


class CartSummaryResponse(BaseModel):
    user_id: int
    distinct_items: int
    total_quantity: int
    total_amount: float
    items: list[CartItemResponse]


class MessageResponse(BaseModel):
    message: str
