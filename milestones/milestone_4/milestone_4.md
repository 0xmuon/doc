# Milestone 4 — payment call with timeout and retry

## Run this copy

This folder is the app as it stood at milestone 4, including `app/`, the Dockerfile, and Compose. It does not import the project root.

```powershell
cd milestones\milestone_4
docker compose up --build
```

Open `http://127.0.0.1:8014/docs`. Postgres on your machine is `localhost:5444` (user `shop`, password `shop`, database `shopping`). The project root stays on port 8000, so this copy can run beside it.


Week 3 milestone 4 is: implement an external API integration with retry and timeout handling.

The external system is a payment gateway. Checkout does not pretend the charge is a column update. It saves the order first, then calls the gateway, then stores what the gateway said. A timeout or a decline does not roll the order back and does not return **500**.

The retry helper in this folder is only used by the payment call. The notification sender, and running it after the response, is milestone 5.

## Why the order is saved first

Postgres can commit the order, the lines, the stock change, and the closed cart in one transaction. The gateway is another process. It cannot join that transaction. The sequence is:

1. Check the open cart, stock, and payment method, as before.
2. Insert the order with `PaymentStatus` `PENDING`, copy prices onto the lines, reduce stock, set the cart to `ORDERED`, and commit.
3. Call `charge_order`.
4. Set `PaymentStatus` to `PAID` or `FAILED` and commit that status by itself.
5. Return **201**. The message is `Order placed successfully` or `Order placed but payment failed`.

Stock stays with the order either way. A failed payment is an unpaid order, not a cancelled one. Retrying payment does not reduce stock again.

If the process dies after step 2 and before step 4, the row is left `PENDING`. `POST /api/payments/process` is how that charge is finished.

## The gateway

`app/integrations/payment_gateway.py` reads:

| Variable | Default | Meaning |
| --- | --- | --- |
| `PAYMENT_API_URL` | empty | Empty means the local stand-in. A URL means a real HTTP POST |
| `PAYMENT_FORCE` | `ok` | `ok`, `fail`, or `timeout`. Used only by the stand-in |
| `PAYMENT_MAX_ATTEMPTS` | `3` | How many tries |
| `PAYMENT_TIMEOUT_SECONDS` | `2` | Passed into each try |

The HTTP body is `order_id`, `amount`, and `payment_method`. A **2xx** response whose JSON `status` is `PAID` succeeds. Anything else, including a timeout, is retried. After the last failure the function returns `FAILED`. It does not raise into the route.

`app/integrations/retry.py` is the loop: call, catch `GatewayError`, sleep a short gap, try again, then raise the last error. The gateway turns that raise into `FAILED` so the order route stays up.

There is no live payment provider in this project. Point `PAYMENT_API_URL` at one when you have one. Until then `PAYMENT_FORCE` is how you show fail and timeout without a network.

## Retry route

`POST /api/payments/process` with `{"order_id": 3}`.

- The caller must be the order's owner and have `order:write`, or an admin (`catalog:manage` stands in for operating on any order).
- Support is **403**.
- A missing order is **404**.
- An order that is already `PAID` is returned as it is. A second click does not charge again.
- `PENDING` or `FAILED` calls the gateway again and stores the new status.

`Orders.PaymentStatus` allows only `PENDING`, `PAID`, and `FAILED`. Orders that existed before this column are set to `PAID` by `app/db/migrate.py`, because those checkouts had no gateway.

## What stays consistent

The order id, the lines, the cart id, and the stock move are committed before the call. The payment status after the call matches the gateway result. A decline is `FAILED`, not a successful response with a paid order, and not an empty **500**.

Customer order history, order details, and `GET /api/admin/orders` all include `payment_status`.
