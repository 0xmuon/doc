# Week 3 interview notes

This is the shopping API after week 2. Week 2 already had register, email login, JWT, products, a cart, and checkout that saved the order and reduced stock. Week 3 keeps that shape and adds passwords that are harder to crack, safer stock and orders, a fake payment and email service, roles, an audit log, and tests.

Say this first if they ask what you did:

> Week 2 was the shopping flow: register, login, browse, cart, checkout. In week 3 I kept email login and the same tables, and I made checkout talk to an external payment API. A failed charge puts the stock back. Email is sent after the response, so a slow notice does not hold the customer. Admins can read an audit log. The one route I converted from sync to async is checkout.

Demo logins, seeded on startup:

| Name | Email | Password | Role |
| --- | --- | --- | --- |
| Rudraksh | rudraksh@example.com | rudraksh1234 | ADMIN |
| Navya | navya@example.com | navya1234 | SUPPORT |
| Het | het@example.com | het12345 | CUSTOMER |

A new registration is always `CUSTOMER`. Only an admin can change a role.

Ports: shopping API `8000`, Postgres on the host `5433`, fake external API `9000`.

```powershell
docker compose up --build
docker compose exec api python -m app.db.seed
```

Swagger for the shop is `http://localhost:8000/docs`. Swagger for the fake API is `http://localhost:9000/docs`. Its title is `fake external apis(notification+payment)`. It has two sections, **Notifications** and **Charges**.

---

## 1. Argon2 passwords, active flag, and who am I

Week 2 stored a PBKDF2 hash (`salt$hex`). Week 3 stores an Argon2 hash. The column is still `Users.Password`, `String(255)`. The hash string starts with `$argon2` and already contains the salt, so there is no separate salt column.

```python
from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(password: str, stored: str) -> bool:
    if stored.startswith("$argon2"):
        return _hasher.verify(password, stored)
    # old salt$hex rows still match until that account is recreated
    salt, digest = stored.split("$", 1)
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return secrets.compare_digest(check.hex(), digest)
```

`GET /api/auth/me` needs the bearer token and returns the user from that token. The password is not in the response. `is_active` is.

Login still uses **email**, not a username. If the password matches and `is_active` is false, the message is `Account is inactive`. A wrong password and a missing user still share one message, so we do not reveal which emails exist.

```python
if user is None or not verify_password(payload.password, user.password):
    raise UnauthorizedException("Invalid email or password")
if not user.is_active:
    raise UnauthorizedException("Account is inactive")
```

The same inactive check runs on refresh and on every protected route. The role in the token can be old, so routes read `Role` from the `Users` row.

---

## 2. Roles and the policy are two different things

A **role** is the label on the person. The database allows only three:

`CUSTOMER`, `ADMIN`, `SUPPORT`

A **policy** is the list of what that label may do. The list is `app/policy/policy.csv`. Casbin reads it. `app/policy/model.conf` only describes the shape of a question: role, resource, action.

| Role | Allowed |
| --- | --- |
| CUSTOMER | Own cart, own orders, own payment, own notification |
| ADMIN | Those, plus every order, catalog changes, role changes, and the audit log |
| SUPPORT | Read every order, and send a notification. No cart, no catalog, no role change, no audit log |

Support reads orders with `GET /api/admin/orders`. There is no `GET /api/orders/{user_id}`. History for the logged-in person is `GET /api/orders/me`. Checkout checks that `user_id` in the body is the token user.

```python
def has_permission(role: str, permission: str) -> bool:
    resource, action = _ACTIONS.get(permission, ("", permission))
    return allow(role, None, resource, action, None)
```

An unknown role is denied. It is not treated as a customer.

---

## 3. Products: SKU, price, stock, and delete

A product now has a unique `SKU`. Price must be above zero. Stock cannot go below zero. Both rules are check constraints on `Products`, and Pydantic also rejects a bad create with `422`.

```python
__table_args__ = (
    CheckConstraint('"Price" > 0', name="ck_products_price_positive"),
    CheckConstraint('"AvailableQuantity" >= 0', name="ck_products_stock_not_negative"),
)
sku: Mapped[str] = mapped_column("SKU", String(30), unique=True, nullable=False)
```

`DELETE /api/admin/products/{product_id}` does not remove the row. It sets `is_active` to false and writes an audit row. The shop list hides inactive products. Adding an inactive product to the cart returns 404.

```python
product.is_active = False
audit_repository.record(db, actor.user_id, "delete", "product", product.product_id, product.sku)
```

---

## 4. One cart line per user and product

Week 2 could create a second line for the same product. Week 3 has a unique constraint on `(UserID, ProductID)`. Adding the same product again keeps the same `CartItemID` and adds the quantity.

```python
UniqueConstraint("UserID", "ProductID", name="uq_user_product_cart")
```

```python
existing = cart_repository.get_by_user_product(db, payload.user_id, payload.product_id)
new_quantity = payload.quantity + (existing.quantity if existing else 0)
if existing:
    existing.quantity = new_quantity
else:
    row = CartItem(user_id=payload.user_id, product_id=payload.product_id, quantity=payload.quantity)
```

Update and remove use `cart_item_id`, not the product id. The cart-summary route is gone.

---

## 5. Orders: two statuses, a number, and a payment reference

Week 2 had one payment status: `PENDING`, `PAID`, `FAILED`. Week 3 keeps that and adds a separate order status.

| Payment status | Order status | Meaning |
| --- | --- | --- |
| PENDING | PENDING_PAYMENT | Stock is reserved, charge has not finished |
| PAID | CONFIRMED | Charge succeeded. `payment_reference` is set, like `PAY-AB12CD34` |
| FAILED | PAYMENT_FAILED | Charge failed. `failure_reason` is set. Stock is released |

The public number is `ORD-000042`, built from the order id after insert. A temporary `TMP-...` value fills the unique column until that id exists.

Checkout order:

1. Lock the product rows with `FOR UPDATE`.
2. Check stock, copy the current price onto each order line, reduce stock, delete the cart lines.
3. Commit that. The order exists before the charge.
4. Call the payment API. The idempotency key is the order number.
5. If the charge is `PAID`, set `CONFIRMED` and store the reference.
6. If it fails, set `PAYMENT_FAILED`, store the reason, and add the quantities back.

```python
async def checkout(db: AsyncSession, payload: CheckoutRequest) -> CheckoutResponse:
    order_id, total, method, number = await db.run_sync(lambda sync_db: _reserve(sync_db, payload))
    outcome = await charge_order(order_id, total, method, number)
    return await db.run_sync(lambda sync_db: _apply_payment(sync_db, order_id, outcome))
```

```python
def _release_stock(order: Order) -> None:
    for line in order.details:
        line.product.available_quantity += line.quantity
```

The charge is **after** the commit on purpose. A timeout must not roll the order back and lose the record. The customer can retry.

Retry of an order that is already `PAID` does not charge again. Retry of a `FAILED` order must reserve the stock again, because the failure already gave it back. If that second charge fails, the stock is released again.

```python
if status == "FAILED":
    await db.run_sync(lambda sync_db: _rehold(sync_db, order_id))
outcome = await charge_order(order_id, amount, method, number)
```

---

## 6. The one function converted from sync to async

Week 2 checkout was a normal `def` and it blocked the worker while it talked to payment. Week 3 checkout is `async def`. That is the route the assignment asked to convert.

The database steps stay synchronous. They use `Session`, row locks, and one transaction. Those helpers run through `await db.run_sync(...)`, so the async session can wait without holding the event loop during the HTTP charge.

These stay normal functions because they use the sync session and return immediately:

- register, login, refresh, `GET /auth/me`
- product list and search, except `GET /api/categories`, which is also async
- cart get, add, update, remove
- order history and order details
- Argon2 hash and verify (they are CPU work, not waiting on the network)

`POST /api/payments/process` is async too. Its database steps also go through `run_sync`.

---

## 7. Payment and email are one fake API on port 9000

Week 2 style was a payment service on its own port. Week 3 has **one** stand-in process for both charges and email.

| Call | URL | What a failure does |
| --- | --- | --- |
| Charge | `http://provider:9000/payments/charge` | Marks the order `PAYMENT_FAILED` and puts stock back |
| Email | `http://provider:9000/notify` | Logged only. The order is not changed |

From your machine those are `localhost:9000`. Modes are only `ok`, `fail`, and `slow`.

```powershell
curl -X PUT http://localhost:9000/mode/ok
curl -X PUT http://localhost:9000/mode/fail
curl -X PUT http://localhost:9000/mode/slow
```

- `ok` returns 200. A charge body includes `status: PAID` and a `reference`.
- `fail` returns **503** with `External API is down`. The shopping API treats 5xx as something to retry.
- `slow` waits 10 seconds, then succeeds. The shopping API timeout is 2 seconds, so slow becomes a failed charge after the retries.

The notice body is only `{order_id, email, payment_status}`.

Checkout sends the notice with `BackgroundTasks`, after the order response is ready. The customer is not waiting on email.

```python
result = await order_service.checkout(db, payload)
background.add_task(
    send_order_notification,
    result.order.order_id,
    current.email,
    result.order.payment_status,
)
return result
```

A repeated charge with the same `Idempotency-Key` returns the same reference and does not create a second payment. The key is the order number.

```python
if key and key in charges:
    saved = charges[key]
    return {"status": "PAID", "reference": saved["reference"], "order_id": body.order_id}
```

If `PAYMENT_API_URL` is empty, tests do not call port 9000. `PAYMENT_FORCE` decides the result: `ok` pays with reference `PAY-LOCAL`, `fail` is a decline, `timeout` is a gateway error.

---

## 8. Retry, timeout, and the circuit breaker

Two kinds of failure:

| Kind | Example | Retry? | Opens the breaker? |
| --- | --- | --- | --- |
| Decline | HTTP 402, or local `PAYMENT_FORCE=fail` | No. The shop said no. | No |
| Gateway error | Timeout, connection error, 408, 503 | Yes, up to 3 times | Yes, after 5 failures |

The wait between tries doubles: about 0.05s, then 0.10s.

```python
except DeclineError:
    raise
except GatewayError as exc:
    delay = base_delay * (2 ** (attempt - 1))
    await asyncio.sleep(delay)
```

The breaker starts **closed** (calls go out). After enough gateway errors it goes **open** and the next call fails immediately. After 30 seconds it goes **half-open** and allows one try. A success closes it again.

`charge_order` does not raise into the route. It returns `PaymentOutcome` with `PAID` or `FAILED`. The order row stays either way.

A failed notification is logged as `order_notification_failed` and is not retried into a change of the order.

---

## 9. Audit log and timestamps

`AuditLogs` records admin catalog changes and each payment result. Only an admin can read it (`audit:read`). Support cannot.

Columns: who (`ActorID`), `Action`, `Resource`, `ResourceID`, `Detail`, `CreatedAt`.

Main rows also have `CreatedAt` and `UpdatedAt`: users, products, cart lines, orders. `UpdatedAt` uses `onupdate=func.now()`.

---

## 10. Database startup

Table names stay quoted, the same names as the earlier weeks: `Users`, `Categories`, `Products`, `CartItems`, `Orders`, `OrderDetails`, `AuditLogs`.

Python attributes stay normal: `user_id`, `product_name`, `available_quantity`. The column name is the quoted one, for example `mapped_column("UserID", ...)`.

On startup the app calls `Base.metadata.create_all`. That creates missing tables. It does not alter a table that already exists. The database is recreated with:

```powershell
docker compose down -v
docker compose up --build
```

`down -v` deletes the Postgres volume. The next boot creates `shopping` empty, then `create_all` and the seed fill it. Seed skips a category, SKU, or email that is already there, so a second boot does not duplicate Rudraksh, Navya, or Het and does not reset their password.

Postgres has a health check (`pg_isready`). The API container waits until that check passes before it starts.

There is one database for the app: `shopping`. Tests use a different database on the same server, `shopping_test`, and they drop and recreate that one. They do not wipe `shopping`. If `DATABASE_URL` starts with `sqlite`, tests use `test_ecommerce.db` instead.

Seed from the command line:

```powershell
docker compose exec api python -m app.db.seed
```

`exec` needs the service name `api`.

---

## 11. Tests, Ruff, and coverage

37 tests. They are not all the same kind.

**Unit tests** call one function, or the fake API alone. No shopping database.

- Argon2 hash and verify
- Role checks (customer cannot manage the catalog, support can read any order)
- Retry stops on a decline and continues on a timeout
- Payment client with a fake network
- Fake charge API and fake email API, including the Swagger sections

**Integration tests** send HTTP into the shopping app and use Postgres. They are marked `integration`.

- Browse, login, cart, support permissions, checkout, retry
- Tokens and `GET /auth/me`
- Inactive user cannot log in
- Same product stays one cart line
- Failed payment puts stock back
- Delete only deactivates a product
- Price of 0 is rejected with 422
- Health, and one live test that the notice reaches port 9000

Ruff checks style (`E` and `F`) using `pyproject.toml`. `.coveragerc` is only for a coverage report. The app and `pytest` run without it. Coverage is a report, not a rule that fails the build.

```powershell
docker compose exec api python -m pytest -q
docker compose exec api python -m ruff check app tests provider
```

---

## 12. Questions they will ask

**Why charge after the commit?**
The order has to exist before we take money. If the charge times out, we still have an order in `PAYMENT_FAILED` and the stock is back. The customer retries that order. We do not create a second order for the same click.

**Why does a failed email not fail the order?**
The customer already paid or already failed payment. Email is a notice. Losing it must not un-pay an order or take the stock away twice.

**What is the idempotency key?**
The order number. The fake API stores the reference for that key. A second POST with the same key returns the same `PAY-...` reference.

**Why is support not an admin?**
Support can read every order, which a customer cannot. Support cannot create products, change roles, or read the audit log. That split is in `policy.csv`, not in an `if role == "ADMIN"` scattered through the routes.

**Why does delete not use SQL DELETE?**
Old order lines point at the product. Deactivating hides it from the shop and keeps history.

**Why `run_sync` inside an async checkout?**
The lock and the stock update need one synchronous transaction. The part that waits is the HTTP charge, and that part is awaited.

**What happens in slow mode?**
The fake API sleeps 10 seconds. Our timeout is 2 seconds, with 3 attempts. Those attempts fail, the breaker may open, and the order ends `PAYMENT_FAILED` with the stock restored.

**What did you leave out on purpose?**
Login stays email, not username. The fake API has no flaky mode, no decline mode, and no rule that amounts over 50,000 are refused. A local decline is `PAYMENT_FORCE=fail`, which becomes HTTP-style `DeclineError` and is not retried. The provider's `fail` mode is 503, which is retried.

---

## 13. File map, if they ask where it lives

| Idea | File |
| --- | --- |
| Argon2 | `app/utils/helpers.py` |
| Me, login, inactive | `app/routers/auth_router.py`, `app/services/user_service.py` |
| Roles | `app/models/user.py`, `app/policy/policy.csv`, `app/utils/permissions.py` |
| SKU, price, stock, active | `app/models/product.py`, `app/services/admin_service.py` |
| One cart line | `app/models/cart.py`, `app/services/cart_service.py` |
| Reserve, release, retry | `app/services/order_service.py` |
| Charge, timeout, breaker | `app/integrations/payment_gateway.py`, `circuit_breaker.py`, `retry.py` |
| Email after the response | `app/routers/order_router.py`, `app/integrations/notification.py` |
| Fake API | `provider/main.py` |
| Audit | `app/models/audit_log.py` |
| Seed | `app/db/seed.py` |
| Startup | `app/main.py` lifespan, `docker-compose.yml` healthcheck |
