"""product response.category_name is filled from the related catagory."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    category_name: str


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    sku: str
    product_name: str
    description: str
    category_id: int
    category_name: str
    price: float
    available_quantity: int
    product_url: str
    is_active: bool


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_name: str = Field(max_length=100)

    @field_validator("category_name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Category name cannot be empty")
        return cleaned


class CategoryUpdate(CategoryCreate):
    pass


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str = Field(max_length=30)
    product_name: str = Field(max_length=200)
    description: str
    category_id: int = Field(gt=0)
    price: Decimal = Field(gt=0)
    available_quantity: int = Field(ge=0)
    product_url: str = ""

    @field_validator("sku")
    @classmethod
    def sku_clean(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("SKU cannot be empty")
        return cleaned

    @field_validator("product_name", "description")
    @classmethod
    def text_not_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value cannot be empty")
        return cleaned


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str | None = Field(default=None, max_length=30)
    product_name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    category_id: int | None = Field(default=None, gt=0)
    price: Decimal | None = Field(default=None, gt=0)
    available_quantity: int | None = Field(default=None, ge=0)
    product_url: str | None = None
    is_active: bool | None = None

    @field_validator("sku")
    @classmethod
    def sku_clean(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("SKU cannot be empty")
        return cleaned

    @field_validator("product_name", "description")
    @classmethod
    def text_not_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value cannot be empty")
        return cleaned
