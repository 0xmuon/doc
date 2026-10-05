"""http only.each file is one group of routes."""

from app.routers import admin_router, auth_router, cart_router, ops_router, order_router, product_router, user_router

__all__ = [
    "admin_router",
    "auth_router",
    "cart_router",
    "ops_router",
    "order_router",
    "product_router",
    "user_router",
]
