# Milestone 2 — roles and reusable permission checks

## Run this copy

This folder is the app as it stood at milestone 2, including `app/`, the Dockerfile, and Compose. It does not import the project root.

```powershell
cd milestones\milestone_2
docker compose up --build
```

Open `http://127.0.0.1:8012/docs`. Postgres on your machine is `localhost:5442` (user `shop`, password `shop`, database `shopping`). The project root stays on port 8000, so this copy can run beside it.


Week 3 milestone 2 is: implement role-based / policy-based authorization with reusable access checks.

The case study names Casbin or equivalent policy logic. This API uses one Python map and FastAPI dependencies. Three roles do not need a second policy server. Routes ask for a permission. They do not write `if role == "admin"`.

The database is the authority. `get_current_user` loads the `Users` row on every protected call and reads `Role` from that row. The JWT may also carry `role` so a client can show the right screen. A demotion applies on the next request, without waiting for the token to expire.

## Roles

One role per user. The column is `Users.Role`, checked to `CUSTOMER`, `ADMIN`, or `SUPPORT`. Register always writes `CUSTOMER`. A body that includes `role` is **422**, because `UserCreate` forbids extra fields.

| Role | What they may do |
| --- | --- |
| Customer | Browse (public), own cart, own checkout, own orders |
| Admin | Everything a customer can do on their own account, plus catalog management, every order, and role changes |
| Support | Read any order. No cart, no checkout, no catalog writes, no role changes |

Browse stays public. An admin is not allowed to open someone else's cart or check out as them. Support has no cart permission at all, even for their own user id, so a support login is a troubleshooting login, not a shopper login.

"Customer issues" has no ticket table in this project. Support's troubleshooting view is order history and order details.

## Permissions

The only map is `ROLE_PERMISSIONS` in `app/utils/permissions.py`.

| Permission | Customer | Admin | Support |
| --- | --- | --- | --- |
| `cart:read`, `cart:write` | yes | yes | no |
| `order:read:own` | yes | yes | yes |
| `order:read:any` | no | yes | yes |
| `order:write` | yes | yes | no |
| `catalog:manage` | no | yes | no |
| `user:role` | no | yes | no |

An unknown role matches nothing, so the call is denied. It is not treated as a customer.

`require_permission("cart:write")` is the reusable check. It depends on `get_current_user`, then raises **403** `You do not have access to this action` when the role lacks that permission.

`require_order_access` is the attribute check on top of the role. Admin and support (`order:read:any`) may pass any user id. A customer may pass only their own, otherwise **403** `You can only access your own orders`. Cart routes still call `require_owner` after the permission check. Permission is checked first, so a support token on a cart returns the permission message, not the "own cart" message.

## The one new route

`PATCH /api/admin/users/{user_id}/role` with `{"role": "SUPPORT"}`.

- Permission `user:role`. Customers and support get **403**.
- Missing user is **404** `User not found`.
- A bad role name is **422**.
- The caller cannot change their own role: **403** `You cannot change your own role`.
- Demoting the last admin is **409** `At least one admin is required`.
- Success is **200** and the user object, including the new `role`. No password.

Catalog write routes are milestone 3. The permission `catalog:manage` exists now so those routes only have to declare it.

## Staff accounts

Startup calls `seed_staff` after the catalog seed. It inserts a user only when that email is missing. It does not reset a password on the next boot.

| Email | Password | Role |
| --- | --- | --- |
| `admin@example.com` | `admin12345` | ADMIN |
| `support@example.com` | `support12345` | SUPPORT |

The values come from `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SUPPORT_EMAIL`, and `SUPPORT_PASSWORD`. If one is empty, that account is skipped. `@shop.local` is rejected by the email checker, so the addresses use `example.com`.

Existing shoppers stay `CUSTOMER`. `app/db/migrate.py` adds `Role` on a database that already has a `Users` table, defaults old rows to `CUSTOMER`, and adds the check constraint. `create_all` does not alter an existing table, and the volume is not wiped.

## How a request is decided

1. Missing or bad token: **401** (milestone 1).
2. Role lacks the permission: **403** `You do not have access to this action`.
3. Customer touching another user's cart or order: **403** own-cart or own-orders.
4. Both pass: the service runs. Stock and empty-cart errors stay **400**. Missing rows stay **404**.

## Files

| File | Change |
| --- | --- |
| `app/models/user.py` | `Role` column |
| `app/utils/permissions.py` | The map |
| `app/utils/deps.py` | `require_permission`, `require_order_access` |
| `app/routers/cart_router.py` | Permission, then owner |
| `app/routers/order_router.py` | Permission, then `require_order_access` |
| `app/routers/admin_router.py` | The role route only, at this milestone |
| `app/services/user_service.py` | Force `CUSTOMER` on register. `change_role` |
| `app/db/seed.py` | `seed_staff` |
| `app/db/migrate.py` | `Role` on an existing Postgres database |

Login responses now include `user.role`. That field is part of this milestone, not milestone 1.
