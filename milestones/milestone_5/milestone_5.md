# Milestone 5 — one async read, a background notice, and request logs

## Run this copy

This folder is the app as it stood at milestone 5, including `app/`, the Dockerfile, and Compose. It does not import the project root.

```powershell
cd milestones\milestone_5
docker compose up --build
```

Open `http://127.0.0.1:8015/docs`. Postgres on your machine is `localhost:5445` (user `shop`, password `shop`, database `shopping`). The project root stays on port 8000, so this copy can run beside it.


Week 3 milestone 5 is: async processing, background tasks, logging, and exception handling.

The rest of the API stays synchronous on purpose. Checkout, cart writes, and payment updates need a normal SQLAlchemy session and one transaction. Making every route `async def` while the driver call still blocks would stall the event loop. Async is used where the work is waiting.

## The async endpoint

`GET /api/categories` was a sync read. It is now `async def` and uses an async SQLAlchemy session (`app/db/async_session.py`).

psycopg 3 speaks asyncio, so the Postgres URL does not change. Tests use sqlite, and that async driver is `aiosqlite`, which is why both packages are in `requirements.txt`. The async engine rewrites a `sqlite://` URL to `sqlite+aiosqlite://` and leaves `postgresql+psycopg://` alone.

The route still returns the same category list. Callers do not see a new path. `GET /api/products` and search stay sync, on the original session, because one converted read is what the milestone asks for and the catalog writes are easier to reason about on the sync session.

Why this route and not checkout: listing categories is a single query with no stock to protect. Checkout must commit order, lines, and stock together. That stays a sync transaction. An async checkout would still have to wait for the same locks, and a mistake in it would double-sell a product.

## Background notification

`POST /api/orders/checkout` queues `send_order_notification` with FastAPI `BackgroundTasks` after the order is saved and the payment status is known. The HTTP response does not wait for the notice.

`POST /api/notifications/send` with `{"order_id": 1}` queues the same function. The caller must be allowed to read that order (the owner, admin, or support). The response is **200** `Notification queued`.

`app/integrations/notification.py` always writes a JSON log line. If `NOTIFY_API_URL` is set, it POSTs `order_id`, `email`, and `payment_status`, with the same retry helper as payments. A failed notice is logged and does not change the order. The default is an empty URL, so development only logs.

The background task runs after the response. It does not hold the request's database session. It does not need one: the ids were already loaded.

## Logs

`app/utils/logging_setup.py` writes one JSON object per line on the `shopping` logger.

Every request gets a 12-character id, stored on a context variable and returned as `X-Request-ID`. The line has `event`, `request_id`, `method`, `path`, `status`, and `ms`. It does not log the `Authorization` header or the body.

Payment results log `payment_result` or `payment_retry` with the order id and the status. Unhandled exceptions log `unhandled_error` with the exception type, and the client still receives **500** `Internal server error`. `AppException` (400, 401, 403, 404, 409) is still a JSON `detail` and is not turned into a 500.

## What is still sync, and why

Cart, checkout, admin writes, and login stay `def` routes. FastAPI runs those in a threadpool, so a blocking Postgres call does not freeze the loop that serves `GET /api/categories`. That split is the tradeoff: async for the read that only waits, sync for the transactions.
