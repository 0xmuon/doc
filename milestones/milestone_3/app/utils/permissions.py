"""role to permission map.routes ask for a permission,they dont name a role."""

CUSTOMER = "CUSTOMER"
ADMIN = "ADMIN"
SUPPORT = "SUPPORT"
ROLES = (CUSTOMER, ADMIN, SUPPORT)

# one place for who can do what.a new role is a new row here,not a new if in every route.
ROLE_PERMISSIONS: dict[str, set[str]] = {
    CUSTOMER: {"cart:read", "cart:write", "order:read:own", "order:write"},
    ADMIN: {
        "cart:read",
        "cart:write",
        "order:read:own",
        "order:read:any",
        "order:write",
        "catalog:manage",
        "user:role",
    },
    SUPPORT: {"order:read:own", "order:read:any"},
}


def has_permission(role: str, permission: str) -> bool:
    """unknown role is deny.allways,never fall back to customer."""
    return permission in ROLE_PERMISSIONS.get(role, set())
