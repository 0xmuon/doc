"""import every model so tables get registred before create_all."""

from app.models.audit_log import AuditLog
from app.models.cart import CartItem
from app.models.category import Category
from app.models.order import Order, OrderDetail
from app.models.product import Product
from app.models.user import User

__all__ = ["AuditLog", "User", "Category", "Product", "CartItem", "Order", "OrderDetail"]
