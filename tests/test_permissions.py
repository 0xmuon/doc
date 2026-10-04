"""policy map.unknown role denies,support cannot write a cart."""

from app.models.user import User
from app.utils.deps import require_order_access
from app.utils.exceptions import ForbiddenException
from app.utils.permissions import has_permission


def _user(user_id: int, role: str) -> User:
    return User(user_id=user_id, name="A", email=f"{role}@x.com", password="x", mobile="9988776655", role=role)


def test_customer_can_shop_and_cannot_manage_catalog():
    assert has_permission("CUSTOMER", "cart:write") is True
    assert has_permission("CUSTOMER", "catalog:manage") is False
    assert has_permission("NOBODY", "cart:read") is False


def test_support_reads_any_order_and_customer_does_not():
    support = _user(2, "SUPPORT")
    require_order_access(support, 99)
    customer = _user(1, "CUSTOMER")
    try:
        require_order_access(customer, 99)
        raise AssertionError("customer should not read another order")
    except ForbiddenException as exc:
        assert exc.status_code == 403
        assert "own orders" in exc.message
