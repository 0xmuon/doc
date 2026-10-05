"""business rules.one module per area,routes call the module not the tables."""

# product_service before admin_service,admin calls into it while this package is still loading.
from app.services import cart_service, order_service, product_service, user_service, admin_service

__all__ = [
    "admin_service",
    "cart_service",
    "order_service",
    "product_service",
    "user_service",
]
