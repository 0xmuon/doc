"""product response.category_name is filled from the related catagory."""

from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    category_name: str


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    description: str
    category_id: int
    category_name: str
    price: float
    available_quantity: int
    product_url: str
