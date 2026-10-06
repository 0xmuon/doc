# Week 3 API demo cases

Start the stack, then open two Swagger pages:

- Shop: `http://localhost:8000/docs`
- Fake payment and email API: `http://localhost:9000/docs`

```powershell
docker compose up --build
```

Logins:

| Who | Email | Password | Role |
| --- | --- | --- | --- |
| Rudraksh | rudraksh@example.com | rudraksh1234 | ADMIN |
| Navya | navya@example.com | navya1234 | SUPPORT |
| Het | het@example.com | het12345 | CUSTOMER |

A person you register in Swagger is a customer. Password at least 8 characters. Mobile is 10 digits. Do not send `role`.

Every protected call needs `Authorization: Bearer <access_token>`. The token comes from login.

These cases were run against the live stack. The automated suite was run in the same session: **37 passed**. Het was set inactive for one check and then turned back on. Provider mode was put back to `ok` at the end.

---

## 1. Health and browse, no token

| Case | Call | Result |
| --- | --- | --- |
| Process is up | `GET /health` | 200 `{"status":"ok"}` |
| Database is up | `GET /health/db` | 200 `{"status":"ok"}` |
| Counters | `GET /metrics` | 200 |
| Product list | `GET /api/products` | 200, seeded products |
| Categories | `GET /api/categories` | 200, and the response has `X-Request-ID` |
| Search | `GET /api/products/search?name=Wireless` | 200 |
| Missing product | `GET /api/products/999999` | 404 |
| Cart with no token | `GET /api/cart/1` | 401 `Valid token is required` |

---

## 2. Register and login

`POST /api/users/register`

```json
{"name": "Demo Buyer", "email": "demo@example.com", "password": "secret123", "mobile": "9988776655"}
```

| Case | Result |
| --- | --- |
| Valid register | 201, `role` is `CUSTOMER`, no password in the body |
| Same email again | 409 `Email must be unique` |
| `"role": "ADMIN"` added to the body | 422 |
| Password shorter than 8 | 422 |
| Wrong password on `POST /api/auth/login` | 401 `Invalid email or password` |
| Right password | 200, `access_token` and `refresh_token` |
| `GET /api/auth/me` with the access token | 200, same email, `is_active` true |
| `GET /api/auth/me` with `Bearer not-a-token` | 401 |
| `POST /api/auth/refresh` with the refresh token | 200, a new access token |
| Refresh using the access token | 401 |
| Het set inactive, then login with the right password | 401 `Account is inactive` |

After that last check, Het was set active again and login returned 200 `CUSTOMER`.

---

## 3. Cart

Use the customer token. `user_id` must be that customer's id from `/api/auth/me`.

`POST /api/cart/add`

```json
{"user_id": 4, "product_id": 2, "quantity": 1}
```

| Case | Result |
| --- | --- |
| First add | 201, a `cart_item_id` |
| Same product added again | 201, same `cart_item_id`, quantity becomes 2 |
| `PUT /api/cart/update/{cart_item_id}` with `{"quantity": 1}` | 200, quantity 1 |
| Admin token opening that customer's cart | 403 |
| Support token opening a cart | 403 |
| `DELETE /api/cart/remove/{cart_item_id}` | 200 `Item removed from cart` |

Quantity `0` is 422. An inactive product is 404.

---

## 4. Checkout when payment is ok

`PUT http://localhost:9000/mode/ok`

`POST /api/orders/checkout` with the customer token:

```json
{"user_id": 4, "payment_method": "UPI"}
```

| Case | Result |
| --- | --- |
| Cart is empty | 400 `User must have at least one cart item before checkout` |
| Payment method `CASH` | 422 |
| Cart has one unit of product 2 | 201 |

The success body has:

- `order_number` like `ORD-000001`
- `payment_status` `PAID`
- `order_status` `CONFIRMED`
- `payment_reference` like `PAY-3A002441`

Checked with that call: stock of product 2 went from 40 to 39, the cart became empty, and `GET http://localhost:9000/sent` contained `{order_id, email, payment_status: PAID}`.

| Follow-up | Result |
| --- | --- |
| `GET /api/orders/me` | 200, that order is in the list |
| `GET /api/orders/details/{order_id}` as the buyer | 200 |
| Same details as Rudraksh (admin) | 200 |
| `GET /api/admin/orders` as the customer | 403 |
| `GET /api/admin/orders` as Navya (support) | 200 |
| `POST /api/payments/process` with `{"order_id": 1}` on the already paid order | 200, same `payment_reference`, still `PAID` |

---

## 5. Roles on admin routes

Rudraksh's token:

| Case | Call | Result |
| --- | --- | --- |
| Create category | `POST /api/admin/categories` `{"category_name": "Demo"}` | 201 |
| Rename it | `PUT /api/admin/categories/{id}` | 200 |
| Price 0 | `POST /api/admin/products` with `"price": 0` | 422 |
| Create product | sku `demo-...`, price 10, quantity 5 | 201, stored SKU is uppercase `DEMO-...` |
| Same SKU again | | 409 `SKU must be unique` |
| Delete | `DELETE /api/admin/products/{id}` | 200, `is_active` false |
| Public fetch of that product | `GET /api/products/{id}` | 404 |
| Audit log | `GET /api/admin/audit-logs` | 200 |
| Change his own role | `PATCH /api/admin/users/{his id}/role` `{"role":"CUSTOMER"}` | 403 |
| Change the demo user to SUPPORT, then back to CUSTOMER | `PATCH /api/admin/users/{id}/role` | 200 both times |

Navya's token:

| Case | Result |
| --- | --- |
| `POST /api/admin/categories` | 403 |
| `GET /api/admin/audit-logs` | 403 |
| `GET /api/admin/orders` | 200 |

---

## 6. Payment down, then retry

`PUT http://localhost:9000/mode/fail`

Add product 2 to the cart again and checkout with `CARD`.

| What to look at | Result seen |
| --- | --- |
| HTTP status of checkout | 201, the order exists |
| `payment_status` | `FAILED` |
| `order_status` | `PAYMENT_FAILED` |
| `failure_reason` | present |
| Stock | unchanged, because the reserved unit was put back |

Then, while the fake API is still in `fail`:

`POST /api/notifications/send`

```json
{"order_id": 2}
```

The response is 200 `Notification queued`. A moment later the order is still `FAILED`. The email failure does not change it.

`PUT http://localhost:9000/mode/ok`

`POST /api/payments/process` with that failed `order_id`.

| What to look at | Result seen |
| --- | --- |
| Status | `PAID` |
| Order status | `CONFIRMED` |
| Reference | a new `PAY-...` value |
| Stock | reduced by 1 again |

Put the fake API back to ok when you are done:

```powershell
curl -X PUT http://localhost:9000/mode/ok
```

---

## 7. The fake API by itself

`http://localhost:9000/docs` shows **Notifications** (`POST /notify`) and **Charges** (`POST /payments/charge`).

| Case | Call | Result |
| --- | --- | --- |
| Charge once | `POST /payments/charge` with header `Idempotency-Key: DEMO-1` | 200, `status` `PAID`, a `reference` |
| Same key again, even after `mode/fail` | same body and header | 200, the same `reference` |
| A new key while mode is `fail` | | 503 `External API is down` |
| `PUT /mode/flaky` | | 422 |
| `PUT /mode/slow`, then a new charge | | waits about 10 seconds, then 200 `PAID` |
| `PUT /mode/ok` | | 200 `{"mode":"ok"}` |

Charge body:

```json
{"order_id": 1, "amount": "10.00", "payment_method": "UPI", "order_number": "DEMO-1"}
```

Notice body:

```json
{"order_id": 1, "email": "demo@example.com", "payment_status": "PAID"}
```

`slow` on a real checkout is different from calling the fake API directly. Checkout gives up after 2 seconds, retries, and then marks the order `PAYMENT_FAILED` and returns the stock. The direct call above used a 20 second wait so the 10 second sleep could finish.

---

## 8. What a good demo order is

1. Login as Het, or register a new customer. Show `/api/auth/me`.
2. Show products with no token. Show the cart returning 401 with no token.
3. Add the same product twice and show one line with quantity 2.
4. Checkout on `mode/ok`. Show `ORD-...`, `PAID`, `CONFIRMED`, and a `PAY-...` reference. Show the cart is empty.
5. Login as Navya. Show `GET /api/admin/orders` works and `POST /api/admin/categories` is 403.
6. Switch the fake API to `fail`, checkout once, and show the stock number is the same as before the click.
7. Switch back to `ok` and call `POST /api/payments/process`. Show `PAID` and the stock down by one.
8. Login as Rudraksh. Show the audit log, then delete a product you created and show the shop no longer lists it.
