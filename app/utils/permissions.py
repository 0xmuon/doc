"""role names stay here.who can do what is asked from casbin,not from a second map."""

from app.policy import allow

CUSTOMER = "CUSTOMER"
ADMIN = "ADMIN"
SUPPORT = "SUPPORT"
ROLES = (CUSTOMER, ADMIN, SUPPORT)

# permission string the routes already use,turned into a casbin resource and action.
_ACTIONS = {
    "cart:read": ("cart", "read"),
    "cart:write": ("cart", "write"),
    "order:read:own": ("order", "read_own"),
    "order:read:any": ("order", "read_any"),
    "order:write": ("order", "write"),
    "catalog:manage": ("catalog", "manage"),
    "user:role": ("user", "role"),
    "audit:read": ("audit", "read"),
}


def has_permission(role: str, permission: str) -> bool:
    """unknown role is deny.allways,never fall back to customer."""
    resource, action = _ACTIONS.get(permission, ("", permission))
    return allow(role, None, resource, action, None)
