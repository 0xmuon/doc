# Milestone 2 — role and policy checks

This is the plan. None of it is in the code yet. Milestone 1 still stands: login returns a JWT, cart and orders need that token, and a token for the wrong `user_id` is **403**.

Week 3 milestone 2 is: implement role-based / policy-based authorization with reusable access checks.

The case study names three jobs:

| Role | Allowed |
| --- | --- |
| Customer | Browse products, manage their own cart, place orders, view their own orders |
| Admin | Manage products and categories, view all orders |
| Support | View orders and customer issues. No product admin rights |

Browse is already public. Product and category write APIs, and `GET /api/admin/orders`, are milestone 3. Milestone 2 builds the checks those routes will call, and it changes who may call the order reads that already exist. It does not add the admin catalog.

---

## What "production level" means here

Three roles and about fifteen routes do not need Casbin, OPA, or a second policy service. The case study says "Casbin or equivalent policy logic." The equivalent that fits this API is one policy module and FastAPI dependencies. Every protected route asks that module. Routers do not grow their own `if role == "admin"` branches.

Decisions to keep when this is built:

1. **One role per user.** A person is a customer, an admin, or support. Not a list of roles. The column is `Role` on `Users`, with a check that allows only `CUSTOMER`, `ADMIN`, and `SUPPORT`.
2. **The database is the authority.** `get_current_user` already loads the `Users` row on every protected call. The role check uses that row. A role stored only inside the JWT would stay valid until the token expired, so a demoted admin would keep admin access for up to 60 minutes. The token may also carry `role` so a client can show the right screen. The server ignores that claim.
3. **Deny unless a permission is granted.** A new protected route must name a permission. There is no silent allow.
4. **The client cannot choose a role.** Register has no `role` field. If a body includes one, the schema rejects it. Only an admin can change a role, through one route described below.
5. **Admin is not a stand-in for another shopper.** An admin can view every order. An admin cannot open someone else's cart, change it, or check out as them. Support is the same for carts, and support cannot check out at all.
6. **Support is read-only on orders.** There is no ticket table in this project. "Customer issues" means support can open any user's order history and any order's lines to troubleshoot. They cannot change products, categories, carts, payments, or roles.
7. **Existing users become customers.** The running database already has rows. Adding `Role` must default those rows to `CUSTOMER`. Do not wipe the Postgres volume.
8. **Ownership stays an attribute check.** That is the ABAC part. "Is this cart mine?" is not a role. `require_owner` from milestone 1 stays for carts. Order reads combine the two: customers pass only for their own `user_id`; admin and support pass for any `user_id` because their role has `order:read:any`.

---

## Permissions

Roles never appear inside route functions. Routes ask for a permission. The map is the only place that connects a role to a permission.

| Permission | Who has it | What it guards |
| --- | --- | --- |
| `cart:read` | Customer, Admin | View cart and cart summary, and only for their own `user_id` |
| `cart:write` | Customer, Admin | Add, update, remove, and only for their own `user_id` |
| `order:read:own` | Customer, Admin, Support | `GET /api/orders/me`, and a customer reading their own history or details |
| `order:read:any` | Admin, Support | Read another user's history, or any order's details |
| `order:write` | Customer, Admin | Checkout, and only for their own `user_id` |
| `catalog:manage` | Admin | Milestone 3 create/update product and category. Defined now, unused until those routes exist |
| `user:role` | Admin | Change another user's role |

Support has neither `cart:read`, `cart:write`, nor `order:write`. A support account that wants to shop needs a separate customer account. That split is what "no product admin, and not a normal shopper session" means for this API. Admin keeps shopping permissions so the admin account can place an order of their own and still be verified end to end.

Catalog reads stay public. They are not permissions. `GET /api/categories`, `GET /api/products`, `GET /api/products/search`, and `GET /api/products/{product_id}` stay exactly as they are, with no token.

---

## Route matrix

This is the full rule after milestone 2. Paths are this project's paths. The week 3 sheet still says `cart_item_id`; this API uses `cart_id` and `product_id`, and that does not change.

| Method | Path | Token | Rule |
| --- | --- | --- | --- |
| POST | `/api/users/register` | No | Always creates `CUSTOMER` |
| POST | `/api/users/login` | No | Same as `/api/auth/login` |
| POST | `/api/auth/login` | No | Returns the token. `user` includes `role` |
| GET | `/api/categories` | No | Public |
| GET | `/api/products` | No | Public |
| GET | `/api/products/search` | No | Public |
| GET | `/api/products/{product_id}` | No | Public |
| GET | `/api/cart/{user_id}` | Yes | `cart:read`, then the path `user_id` must be the token user |
| GET | `/api/cart/{user_id}/summary` | Yes | Same as view cart |
| POST | `/api/cart/add` | Yes | `cart:write`, then body `user_id` must be the token user |
| PUT | `/api/cart/update/{user_id}/{product_id}` | Yes | `cart:write`, then path `user_id` must be the token user |
| DELETE | `/api/cart/remove/{user_id}/{product_id}` | Yes | Same as update |
| POST | `/api/orders/checkout` | Yes | `order:write`, then body `user_id` must be the token user |
| GET | `/api/orders/me` | Yes | `order:read:own`. Always the token user's orders, for every role |
| GET | `/api/orders/{user_id}` | Yes | Customer: `order:read:own` and path `user_id` must match. Admin and Support: `order:read:any`, any `user_id` |
| GET | `/api/orders/details/{order_id}` | Yes | Load the order. Customer: order's `user_id` must match, otherwise **403**. Admin and Support: allowed. Missing order stays **404** |
| PATCH | `/api/admin/users/{user_id}/role` | Yes | `user:role` only. This is the one new route |

Milestone 3 will hang these on `catalog:manage`, and they are not part of this work:

- `POST /api/admin/products`
- `PUT /api/admin/products/{id}`
- `POST /api/admin/categories`
- `PUT /api/admin/categories/{id}`
- `GET /api/admin/orders`

Until those exist, an admin proves the role by reading another user's orders and by changing a role. A support user can read any order and must receive **403** on cart, checkout, and role change.

---

## How one request is decided

Same pipeline as today: schema, then router dependency, then service, then repository. The new work sits in the dependency, before the service.

1. No `Authorization` header, or the scheme is not `Bearer` → **401** `Valid token is required`.
2. Bad signature, expired token, garbage `sub`, or no such user → **401** `Invalid or expired token`.
3. User exists. Read `user.role` from that row. Do not read `role` from the JWT payload.
4. The route's permission is missing from that role → **403** `You do not have access to this action`.
5. The route also has an owner rule (every cart route, checkout, and a customer's order read). Token user and target `user_id` differ → **403** `You can only access your own cart` or `You can only access your own orders`.
6. Both checks pass. The service runs. Stock errors, empty cart, and missing products stay **400** or **404** as they are now.

**401** still means "we do not know who you are." **403** means "we know who you are, and this action is not yours." A customer token on an admin route is **403**, not **401**. A support token on `POST /api/cart/add` is **403** even when the body `user_id` is their own, because support has no cart permission. Check the permission first, then ownership, so the message matches the real reason.

Order details keep today's order: find the order, **404** if it is missing, then the role and owner check. A customer probing random ids learns that some orders exist. That matches milestone 1 and makes the check visible. Hiding other people's orders behind **404** would be a later hardening choice, not this milestone.

`GET /api/orders/me` never takes a path id, so support and admin use it for their own shopping history. Troubleshooting another customer is `GET /api/orders/{user_id}` and `GET /api/orders/details/{order_id}`.

---

## Data model

Add one column to `Users`. No new table. A join table would matter if one person held several roles. This case study does not say that.

| Column | Type | Rule |
| --- | --- | --- |
| `Role` | `String(20)`, not null | `CUSTOMER`, `ADMIN`, or `SUPPORT`. Default `CUSTOMER` |

Quoted identifier, same style as `UserID` and `Email`. Check constraint name `ck_user_role`. Index is optional; the table is small and lookups are by primary key after the token is decoded.

`create_all` will not alter the table that is already in Docker. The migration, applied once to the running database, is:

```sql
ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS "Role" VARCHAR(20);
UPDATE "Users" SET "Role" = 'CUSTOMER' WHERE "Role" IS NULL;
ALTER TABLE "Users" ALTER COLUMN "Role" SET DEFAULT 'CUSTOMER';
ALTER TABLE "Users" ALTER COLUMN "Role" SET NOT NULL;
ALTER TABLE "Users" DROP CONSTRAINT IF EXISTS ck_user_role;
ALTER TABLE "Users" ADD CONSTRAINT ck_user_role CHECK ("Role" IN ('CUSTOMER', 'ADMIN', 'SUPPORT'));
```

Do not run `docker compose down -v`. That deletes users, orders, and the catalog.

The SQLAlchemy model gains `role` mapped to `"Role"`. New registers pass `role="CUSTOMER"` in code even though the default exists, so a forgotten default cannot insert a null if the constraint is ever dropped.

---

## The reusable checks

New file `app/utils/permissions.py`. It owns the map and two helpers. `app/utils/deps.py` keeps `get_current_user` and `require_owner`, and it calls into the policy file.

Intended shape:

```python
CUSTOMER = "CUSTOMER"
ADMIN = "ADMIN"
SUPPORT = "SUPPORT"

ROLE_PERMISSIONS = {
    CUSTOMER: {"cart:read", "cart:write", "order:read:own", "order:write"},
    ADMIN: {
        "cart:read", "cart:write",
        "order:read:own", "order:read:any", "order:write",
        "catalog:manage", "user:role",
    },
    SUPPORT: {"order:read:own", "order:read:any"},
}

def require_permission(permission: str):
    def checker(current: User = Depends(get_current_user)) -> User:
        allowed = ROLE_PERMISSIONS.get(current.role, set())
        if permission not in allowed:
            raise ForbiddenException("You do not have access to this action")
        return current
    return checker
```

A route then declares what it needs:

```python
current: User = Depends(require_permission("cart:write"))
require_owner(current, user_id, "cart")
```

`require_permission` already depends on `get_current_user`, so the router-level `Depends(get_current_user)` can stay. FastAPI runs that dependency once per request. Cart routes use `cart:read` or `cart:write` plus `require_owner`. Checkout uses `order:write` plus `require_owner` on `payload.user_id`.

Order history needs a slightly wider helper, because admin and support may pass a `user_id` that is not theirs:

```python
def require_order_access(current: User, user_id: int) -> None:
    allowed = ROLE_PERMISSIONS.get(current.role, set())
    if "order:read:any" in allowed:
        return
    if "order:read:own" in allowed and current.user_id == user_id:
        return
    if "order:read:own" in allowed:
        raise ForbiddenException("You can only access your own orders")
    raise ForbiddenException("You do not have access to this action")
```

Order details call the same helper with `order.user_id` after the **404** check. One function, two routes. That is the reusable access check the milestone asks for.

`GET /api/orders/me` only needs `require_permission("order:read:own")`.

If `current.role` is ever a value outside the map (a bad manual update that slipped past the check), `ROLE_PERMISSIONS.get` returns an empty set and the call is **403**. Unknown role is deny, not customer.

---

## Register, login, and the token

`UserCreate` stays `name`, `email`, `password`, `mobile`. No `role`. Pydantic's default is to ignore extra fields; for this route, set the model to forbid extras so `{"role": "ADMIN"}` on register is **422**, not a silent customer. That is the production choice: a client cannot discover that the field was dropped and assume it worked.

`register_user` sets `role="CUSTOMER"` on the `User` it builds.

`UserResponse` gains `role`. Register and login both return it. Password still never appears.

`create_access_token` may add `"role": user.role` next to `sub`, `email`, and `exp`. `decode_access_token` and `get_current_user` must not authorize from it. After a role change, the next request sees the new role immediately because the row is loaded again. The old claim inside the token is stale on purpose.

Login responses otherwise stay as milestone 1: `message`, `access_token`, `token_type` `bearer`, and `user`. Both `POST /api/users/login` and `POST /api/auth/login` keep sharing `login_user`.

---

## Changing a role

Seeded admin and support accounts are how the three roles first appear. A running shop also needs a way to promote someone without editing SQL.

`PATCH /api/admin/users/{user_id}/role`

```json
{"role": "SUPPORT"}
```

- Token required, permission `user:role`. Customers and support get **403**.
- Path `user_id` must exist, otherwise **404** `User not found`.
- Body `role` must be one of the three names, otherwise **422**.
- Response **200** with the updated `UserResponse` (no password).
- The caller cannot change their own role. **403** `You cannot change your own role`. That stops the last admin from demoting themselves and locking the API.
- The caller cannot demote the last remaining admin. If the target is an admin and the new role is not `ADMIN`, count admins first. One admin left → **409** `At least one admin is required`.
- Promoting a user does not touch their cart or orders.

This route is authorization, not the milestone 3 catalog. It lives on a small `admin_router` with prefix so milestone 3 can add product routes beside it. Tag it `Admin`.

Service method `change_role` does the last-admin count and the update. The router only checks the permission and refuses a self-change. Counting admins belongs in the repository (`count_by_role`).

---

## Seed accounts

Catalog seed returns immediately once any category exists, so it will not insert users into the current database. Role seed is a separate function called from the same startup path, and it is safe to run every boot.

It creates a user only when that email is absent. It never resets a password on later boots, so a changed dev password stays changed.

Put the emails and passwords in `.env`, documented in `.env.example`. Suggested local values, not production secrets:

```
ADMIN_EMAIL=admin@shop.local
ADMIN_PASSWORD=admin12345
SUPPORT_EMAIL=support@shop.local
SUPPORT_PASSWORD=support12345
```

Both passwords meet the 8-character register rule. Names can be `Shop Admin` and `Shop Support`. Mobile values must be 10 digits and unique enough not to matter; mobile is not unique in the schema today. If either env var is missing, skip that account and log a warning. Do not crash startup, and do not invent a hardcoded password inside Python when the env var is empty.

Hash them with the existing `hash_password`. Store `Role` as `ADMIN` or `SUPPORT`.

Existing shoppers, including accounts created during milestone 1, stay `CUSTOMER` because of the column default. Do not promote them.

---

## Files to change when this is built

| File | Change |
| --- | --- |
| `app/models/user.py` | `role` column and the check constraint |
| `app/utils/permissions.py` | New. Role names, the permission map, `require_permission`, `require_order_access` |
| `app/utils/deps.py` | Cart and checkout keep using `require_owner`. No role logic copied into this file beyond calling the policy helpers |
| `app/utils/security.py` | Optional `role` claim in `create_access_token`. Decode path unchanged |
| `app/schemas/user_schema.py` | `role` on `UserResponse`. `RoleUpdate` body. `UserCreate` forbids extra fields |
| `app/services/user_service.py` | Force `CUSTOMER` on register. `change_role` |
| `app/repositories/user_repository.py` | `count_by_role`, update role |
| `app/routers/cart_router.py` | `require_permission` before `require_owner` |
| `app/routers/order_router.py` | Checkout permission plus owner. History and details use `require_order_access` |
| `app/routers/admin_router.py` | New. Only the role route for this milestone |
| `app/main.py` | Include the admin router at prefix `/api`. Description mentions roles |
| `app/db/seed.py` | `seed_staff()` separate from the catalog seed |
| `.env.example` | Admin and support email and password |

No new dependency in `requirements.txt`. No test folder. Tests are milestone 6. No Casbin package.

Comments stay in the same style as the rest of `app/`: lowercase, short, and only where the rule is not obvious (why the JWT role claim is ignored, why self-demotion is blocked).

---

## Order to build it

1. Add the column on the model and run the `ALTER TABLE` against the existing database.
2. Add the policy module and wire `require_permission` with no route changes yet. App still boots.
3. Put `role` on the user response and force `CUSTOMER` on register. Login of an old user returns `"role": "CUSTOMER"`.
4. Apply the cart and checkout checks. A customer token behaves as it does today. A support token on cart or checkout returns **403** before any cart row is touched.
5. Switch order history and order details to `require_order_access`. Customer behavior stays. Admin and support can read across users.
6. Add the role route and the last-admin guard.
7. Add `seed_staff` and the env vars. Restart the API so the two staff users exist.
8. Walk the scenarios below. Do not start milestone 3 in the same change.

---

## Scenarios that must pass

Use three tokens: a normal registered user, `admin@shop.local`, and `support@shop.local`.

Customer, same as milestone 1:

- Own cart and own checkout succeed.
- Another user's cart id in the path or body is **403** `You can only access your own cart`.
- Another user's order history, or another user's order details, is **403** `You can only access your own orders`.
- `PATCH /api/admin/users/{id}/role` is **403** `You do not have access to this action`.
- Register with an extra `role` field is **422**.
- Product list with no token is still **200**.

Admin:

- `GET /api/orders/{customer_id}` and that customer's order details are **200**.
- `GET /api/orders/me` returns only the admin's own orders, which may be an empty list.
- Cart for the admin's own `user_id` works. Cart for the customer's `user_id` is **403**.
- Checkout with the customer's `user_id` is **403**.
- Promote the customer to `SUPPORT`, call an order read with the customer's old token, and get support behavior on the next request without logging in again.
- Demote them back to `CUSTOMER` and the next order read of someone else is **403** again.
- Admin changing their own role is **403**.
- With only one admin in the table, demoting that other admin is **409** if they are the last one. With two admins, demoting the other to `CUSTOMER` is **200**.

Support:

- Any user's order history and any order details are **200**.
- Cart, checkout, and role change are **403** `You do not have access to this action`, including when the cart `user_id` is the support user's own id.
- Browse with no token is **200**.

Shared:

- Missing token on cart or orders is still **401**.
- A forged or expired token is still **401**.
- Login still uses one message for a bad email and a bad password.

After a role change, call the affected route with the same access token. The new role applies on that call. That is the check that the JWT claim is not the authority.

---

## What this milestone still will not do

- No create, update, or delete of products or categories.
- No `GET /api/admin/orders`. Cross-user history uses the existing `GET /api/orders/{user_id}`.
- No payment, shipment, or notification calls.
- No async routes, background tasks, or structured logging milestone. A single warning log on **403** is optional and not a substitute for milestone 5.
- No refresh token.
- No tests and no coverage report.
- No ticket or "customer issue" table. Support's troubleshooting view is the order.
- No second role on one user, and no permission editor. Changing policy means changing `ROLE_PERMISSIONS` in code, which is the right size until the rules outgrow this file.
