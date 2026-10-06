# Week 3 concepts, walked through

You already know week 2: register, email login, JWT, products, cart, and checkout that saves an order and reduces stock. Week 3 asks you to make that API safer, to control who can do what, to call an outside payment and email service without freezing the request, and to prove it with tests.

Read one section, then say the short answer out loud. The code under it is the real code, shortened.

Two sources are mixed in this file:

- **From the week 3 PDF.** The assignment: JWT, roles, a policy, admin APIs, an external payment and email call, retry, timeout, a circuit breaker, one async route, background work, logs, and tests.
- **From ecommerce2.** Extra design we copied because it makes those requirements solid: Argon2, `is_active`, SKU, stock rules, order number, releasing stock on a failed charge, one fake API on port 9000, an audit log, Ruff, and a coverage config.

---

## How the PDF is split

| Milestone | What they want | Where we did it |
| --- | --- | --- |
| 1 | JWT login and protected routes | `app/utils/security.py`, `app/utils/deps.py`, `app/routers/auth_router.py` |
| 2 | Roles and a policy, reused on every route | `app/policy/policy.csv`, `app/utils/permissions.py` |
| 3 | Admin products, categories, and all orders | `app/routers/admin_router.py` |
| 4 | External API, retry, timeout | `app/integrations/`, `provider/main.py` |
| 5 | Async checkout, background email, logs, errors | `app/services/order_service.py`, `app/routers/order_router.py`, `app/main.py` |
| 6 | Unit tests, integration tests, coverage, Git | `tests/`, `pyproject.toml`, `.coveragerc` |

---

## 1. JWT and protected routes

A login checks the email and the password, then returns two tokens: an access token and a refresh token. Cart, checkout, and admin routes read the access token from `Authorization: Bearer ...`. Browse stays open.

The token is not trusted by itself. The route loads the user row, because the role in an old token can be wrong, and an inactive user must be refused.

```python
payload = decode_access_token(credentials.credentials)
user = user_repository.get_by_id(db, int(payload.get("sub")))
if user is None or not user.is_active:
    raise UnauthorizedException("Invalid or expired token")
```

`POST /api/auth/refresh` accepts only the refresh token. Sending the access token there returns 401.

Say: "Missing token is 401. A bad token is 401. A logged-in user who is not allowed is 403."

---

## 2. Argon2, from ecommerce2

Week 2 stored `salt$hex` from PBKDF2. ecommerce2 stores an Argon2 hash with `pwdlib`. We did the same. The salt sits inside the hash string, which starts with `$argon2`. Old PBKDF2 rows still verify until that account is recreated.

```python
_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return _hasher.hash(password)
```

`GET /api/auth/me` returns the token's user, including `is_active`, and never the password.

---

## 3. Role versus policy

A role is the label on the user: `CUSTOMER`, `ADMIN`, or `SUPPORT`. A new signup is always `CUSTOMER`. Sending `"role": "ADMIN"` on register is 422.

The policy is `app/policy/policy.csv`. Each line is one permission. Casbin answers "may this role do this action?"

| Role | Policy allows |
| --- | --- |
| CUSTOMER | Own cart, own orders, own payment, own notice |
| ADMIN | Those, plus catalog, every order, role changes, audit log |
| SUPPORT | Every order, and a notice. No catalog, no cart, no audit log |

```python
def has_permission(role: str, permission: str) -> bool:
    resource, action = _ACTIONS[permission]
    return allow(role, None, resource, action, None)
```

`require_permission("catalog:manage")` is the reusable check. Routes pass the permission name. They do not repeat `if role == "ADMIN"`.

ABAC is the extra part of the same file: a customer may read an order only when `user_id == owner_id`. Admin and support may read any order. That is a rule about the row, not only the role.

---

## 4. Admin product and category APIs

From the PDF: create and update a product, deactivate it, create and update a category, and list every order. Only the allowed role gets in.

From ecommerce2 we also store a unique SKU, reject a price of 0, and refuse negative stock. Delete sets `is_active` to false. The public product list hides that row. Order history still points at it.

```python
CheckConstraint('"Price" > 0', name="ck_products_price_positive")
CheckConstraint('"AvailableQuantity" >= 0', name="ck_products_stock_not_negative")
```

```python
product.is_active = False
audit_repository.record(db, actor.user_id, "delete", "product", product.product_id, product.sku)
```

Support calling `POST /api/admin/categories` is 403. A price of 0 is 422. A repeated SKU is 409.

---

## 5. One cart line per user and product

From ecommerce2. The table has `UniqueConstraint("UserID", "ProductID")`. Adding the same product again keeps the same `CartItemID` and adds the quantity. Update and remove use that line id.

---

## 6. External payment and email

The PDF asks for at least one outside service, with retry and timeout, and a failure that does not crash the order.

We have one fake process on port 9000, the ecommerce2 shape. Charges go to `/payments/charge`. Email goes to `/notify`. Modes are only `ok`, `fail`, and `slow`.

| Mode | Fake API | What our API does |
| --- | --- | --- |
| ok | 200, and a charge includes `reference` | Order becomes `PAID` / `CONFIRMED` |
| fail | 503 `External API is down` | Retried. Then the order is `FAILED` / `PAYMENT_FAILED` and stock comes back |
| slow | sleeps 10 seconds, then 200 | Our timeout is 2 seconds, so the charge fails the same way as a timeout |

The idempotency key is the order number. The same key returns the same `PAY-...` reference and is not charged twice.

```python
headers = {"Idempotency-Key": idempotency_key}
if response.status_code == 402:
    raise DeclineError("Payment gateway declined")
if response.status_code >= 500 or response.status_code == 408:
    raise GatewayError(f"Payment gateway returned {response.status_code}")
```

A decline is a no. We do not retry a no. A timeout or a 503 might be temporary, so we retry up to 3 times. The pause doubles: 0.05s, then 0.10s.

Local tests leave `PAYMENT_API_URL` empty. Then `PAYMENT_FORCE=fail` is a decline, and `PAYMENT_FORCE=timeout` is a gateway error. Docker points both URLs at `http://provider:9000`.

We did not copy ecommerce2's extra modes: flaky, decline, or "amount over 50,000 is refused."

---

## 7. Circuit breaker

This is the piece to be able to draw.

The breaker sits in front of the payment call. It remembers recent gateway failures in memory. A decline does not count.

| State | Meaning |
| --- | --- |
| closed | Normal. Calls go out. |
| open | Too many gateway failures. The next call fails immediately and does not wait on the network. |
| half-open | 30 seconds have passed. One call is allowed. Success closes it. Another gateway error opens it again. |

```python
if self.state == "open":
    if time.monotonic() - self.opened_at < self.reset_seconds:
        raise CircuitOpenError(f"{self.name} circuit breaker is open")
    self.state = "half-open"
```

Default: 5 gateway failures open it, and it stays open for 30 seconds. `charge_order` catches that and returns `FAILED`. The route still responds. The order row stays.

Say: "A decline is an answer. A timeout is an outage. Only the outage opens the breaker."

---

## 8. Order status and giving stock back

Week 2 had only `PENDING`, `PAID`, and `FAILED`, and stock stayed reduced after a decline. ecommerce2 splits the story:

| Payment status | Order status | Stock |
| --- | --- | --- |
| PENDING | PENDING_PAYMENT | Reserved |
| PAID | CONFIRMED | Stays reduced. `payment_reference` is saved |
| FAILED | PAYMENT_FAILED | Added back. `failure_reason` is saved |

Checkout commits the order **before** the charge. A timeout must not delete the order. The public number is `ORD-000001`.

Retry of a `PAID` order does not charge again. Retry of a `FAILED` order reserves the stock again, then charges. If that charge fails, the stock is released again.

The email body is only `{order_id, email, payment_status}`. It is queued with `BackgroundTasks` after checkout, so the customer is not waiting on it. If the notice fails, we log `order_notification_failed` and leave the order as it is.

---

## 9. The one sync route we made async

The PDF says convert at least one existing synchronous flow. That flow is checkout.

`async def checkout` awaits the payment HTTP call. The database work stays in normal functions because it needs one transaction and `FOR UPDATE` locks. Those functions run through `await db.run_sync(...)`.

Sync is still right for login, cart, product search, and Argon2. Those finish immediately and do not wait on another service. Marking them `async` would not make them faster.

`GET /api/categories` and `POST /api/payments/process` are async as well. Payment processing uses `run_sync` for the same reason as checkout.

---

## 10. Logs, errors, and health

Every error we raise ourselves becomes `{"detail": "...", "request_id": "..."}`. An unexpected crash is logged and returned as a plain 500, so the traceback does not leave the server.

`RequestLogMiddleware` puts `X-Request-ID` on the response. `/health` is the process. `/health/db` runs `SELECT 1`. `/metrics` is a small counter report.

Postgres in Compose has a health check, `pg_isready`. The API container does not start until that check passes. That health check is from ecommerce2.

---

## 11. Audit log and timestamps

ecommerce2 records important changes. We write an audit row when an admin creates, updates, or deactivates a product, and when a payment result is saved. Only an admin can `GET /api/admin/audit-logs`.

Users, products, cart lines, and orders have `CreatedAt` and `UpdatedAt`.

---

## 12. Seed that skips existing rows

ecommerce2's seed does not insert a row that is already there. Ours does the same, with our own categories and products. Users are Rudraksh (admin), Navya (support), and Het (customer). A second boot does not reset their password.

```powershell
docker compose exec api python -m app.db.seed
```

Startup is `create_all`, then seed. `create_all` builds missing tables. It does not alter an old table. A fresh database is `docker compose down -v` and then `docker compose up --build`.

Table names stay the quoted week 2 names: `Users`, `Products`, `Orders`, and the rest. ecommerce2 used plain names such as `users`. We did not switch.

---

## 13. Tests

The PDF asks for unit tests, integration tests, mocks, and coverage of the main flows.

| Kind | What it does here | Examples |
| --- | --- | --- |
| Unit | One function, or the fake API alone. No shopping database. | Argon2, the policy, retry, the circuit breaker, the fake charge API |
| Integration | HTTP into the shopping app and Postgres `shopping_test` | Login, cart merge, failed payment puts stock back, support cannot edit the catalog |

The payment unit tests use a fake network (`httpx.MockTransport` in `tests/fakes.py`). They do not open a socket.

`.coveragerc` is from ecommerce2, with one change. Their file fails the run below 85 percent. Ours only shapes the report: measure `app`, show missing lines. `pytest` without `--cov` never reads it. The app runs either way.

---

## 14. Ruff, from ecommerce2

Ruff is the linter. ecommerce2 turns on many rule families. We kept the same tool and a smaller set: pycodestyle `E` and pyflakes `F`, line length 120, Python 3.12. Settings live in `pyproject.toml`.

```powershell
docker compose exec api python -m ruff check app tests provider
```

Two ignores are deliberate. Models use quoted relationship names, which Ruff would call undefined. `tests/conftest.py` sets `DATABASE_URL` before it imports the app.

---

## 15. What we copied, and what we left

Copied from ecommerce2: Argon2, `is_active`, `/auth/me`, SKU, price and stock checks, deactivate on delete, one cart line, order number and the two statuses, stock released on a failed charge, retry that reserves again, one provider on port 9000, idempotency, audit log, timestamps, Postgres health check, service tests, Ruff, and `.coveragerc`.

Left behind: login by username, flaky and decline modes, declining amounts over 50,000, plain table names, a coverage number that fails the build, and their wider Ruff rule set.

---

## 16. One paragraph if they say "explain the payment"

Checkout locks the products, copies the price, reduces stock, deletes the cart lines, and commits. Then it calls port 9000 with the order number as the idempotency key. A 503 or a timeout is retried up to three times. Five of those outages open the circuit breaker for 30 seconds. A decline is not retried. Success stores `PAY-...` and sets the order to `CONFIRMED`. Failure stores the reason, sets `PAYMENT_FAILED`, and puts the stock back. The email is a background task. If that email fails, the order stays as it is.
