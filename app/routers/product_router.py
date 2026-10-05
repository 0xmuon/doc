"""product routes./search is registred before /{product_id} so search is not taken as an id."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db import get_async_db, get_db
from app.schemas import CategoryResponse, ProductResponse
from app.services import product_service

router = APIRouter(tags=["Products"])


@router.get("/categories", response_model=list[CategoryResponse], summary="Categories")
async def list_categories(db: AsyncSession = Depends(get_async_db)):
    # this read waits on the database,so it uses the async session.
    return await product_service.list_categories_async(db)


@router.get("/products", response_model=list[ProductResponse], summary="Products")
def list_products(db: Session = Depends(get_db)):
    return product_service.list_products(db)


@router.get("/products/search", response_model=list[ProductResponse], summary="Search")
def search_products(
    name: str | None = Query(default=None),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return product_service.search_products(db, name, category)


@router.get("/products/{product_id}", response_model=ProductResponse, summary="Product")
def get_product(product_id: int, db: Session = Depends(get_db)):
    return product_service.get_product(db, product_id)
