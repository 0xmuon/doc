# Limits of this shopping API

This note is older than the current app. Stock is released when a charge fails, startup does not run a migrate script, passwords are Argon2, and an audit log exists. Use `WEEK3_LIMITS.md` for the limits that are true now.

This file is about the project as it runs today: one FastAPI app, one Postgres database, Docker Compose, and the week 3 features (JWT, Casbin, async checkout, payment retry, metrics, tests).

It is a solid case-study API. It is not a system you would put in front of a large catalog or a sale with thousands of checkouts at once. Each section is a limit that exists in this code, why it matters when traffic or data grows, and the change that removes it.

## What it can hold

One API process and one Postgres instance are enough for a demo, a class review, and light internal use. Product browse, a cart, checkout, and an admin catalog all work. The seams below show up when you add a second API container, a second checkout at the same moment, or a catalog that no longer fits in one query.

## One process, one database

`docker-compose.yml` starts one API container and one Postgres container. The API command is a single Uvicorn process with `--reload`. Compose starts the API when the database container has started, not when Postgres is ready to accept connections. A fast boot can fail table creation and need a restart.

There is no connection-pool size, no read replica, and no second API instance. Every cart write, checkout, and admin list shares that one database.

At a larger size, run more than one API process behind a load balancer, wait for Postgres with a health check, and set a pool size that matches those processes. Reads of the catalog can go to a replica. Writes (stock, orders, cart) stay on the primary.

## Schema changes are startup scripts

Tables are created with `create_all` when the app starts. Extra columns are added by `ensure_columns` in `app/db/migrate.py`. There is no migration history (no Alembic or equivalent). `create_all` does not change a column that already exists. The cart rebuild drops old cart tables when it still sees a `CartID` column.

Two people shipping schema changes will not have a reviewed, ordered history of those changes. A bad start can drop cart lines. A new column that needs a backfill is a hand-written SQL string.

Use versioned migrations that run as their own step, before the API serves traffic. Do not drop data from application startup.

## Most routes still block a worker

Checkout, payment retry, `GET /api/categories`, and `GET /health/db` use an async session. Cart, login, product list, search, and admin writes still use a normal sync session. Uvicorn runs those sync routes in a thread pool. Under a burst of cart updates, that pool fills and new requests wait even if the event loop is idle.

Password hashing (PBKDF2) also runs on the request that is logging in. A slow hash is good for security and bad if many logins share a small thread pool.

Move the hot paths (cart, catalog read, login) to the async session, and run the hash in a worker thread so it does not sit on the database pool. Keep one style of session for a request so a checkout does not depend on two engines seeing the same commit.

## Catalog and history have no pages

`GET /api/products`, search, and order history return the full list. There is no `limit` or cursor. Ten products is fine. A hundred thousand products means a large query, a large JSON body, and a slow admin screen.

Add cursor or offset pagination, and indexes that match the search filters (name, category, active flag). At a larger catalog, put search in a search engine and keep Postgres as the source of the row.

## Stock is not reserved in the cart

A cart line does not hold stock. Stock drops when checkout commits. Checkout locks the product rows (`FOR UPDATE`) so two checkouts cannot both take the last unit.

If payment then fails, the stock stays reduced. The order is `FAILED` and a retry does not reduce stock again. That avoids selling the same unit twice, and it also means a declined card holds inventory until someone restocks or cancels the order. There is no cancel route and no job that releases `FAILED` or stuck `PENDING` orders.

A sale needs a reservation with an expiry: hold stock for a few minutes, release it if payment fails or the customer leaves, and a background job for orders that stayed `PENDING` because the process died after the commit and before the gateway answered.

## Checkout can be submitted twice

The gateway call sends an `Idempotency-Key` of the order id, so the gateway can refuse a second charge for that order. The API itself does not. Two clicks on checkout create two orders, two stock drops, and two charges. The key is only as good as the gateway. This app does not store keys of its own.

Store a client key (or a hash of user, cart, and total) and return the existing order when the same checkout is repeated.

## Payment state lives in the API process

The circuit breaker and `/metrics` are Python dicts in memory. They reset when the process restarts. A second API container has its own breaker and its own counters. Five failures on one container do not stop the other from calling a dead gateway. `/metrics` is not Prometheus format and is not scraped into a store.

`GET /health` only checks that the process can answer. `GET /health/db` runs `SELECT 1`. Neither checks the gateway.

Put the breaker in a shared store (Redis is the usual choice) or accept one breaker per instance and alert on the error rate from a real metrics system. Export counters in a format a scraper can collect. Make readiness fail when the database is down or the breaker has been open for too long.

## Notifications are not durable

Checkout queues `send_order_notification` with FastAPI `BackgroundTasks`. The task runs in the same process after the response. If the process stops, the notice is gone. A failure is logged and does not undo the order, which is right for the order, and it means the customer may never get the mail. There is no retry queue and no dead-letter list.

Use a real queue (and a worker that is not the API process) for mail and any other work that must happen after checkout. Keep the HTTP response independent of that worker.

## Tokens cannot be revoked

Login returns an access token (default 60 minutes) and a refresh token (default 7 days). Both are signed JWTs. Nothing is stored server-side. You cannot log a user out of other devices, rotate a stolen refresh token, or reject a token before it expires. The role inside the token is ignored and the `Users` row is loaded on each call, so a role change applies on the next request. A stolen access token still works until `exp`.

The default secret in code is `change-this-shopping-secret-key-32b` if `JWT_SECRET` is missing. Anyone who can guess that secret can mint tokens.

Keep access tokens short. Store refresh tokens (hashed) so a logout or a password change deletes them. Issue a new refresh token on each refresh and reject the old one. Require a real secret in production and refuse to start when the default is still set.

## Casbin is a file on one machine

`app/policy/policy.csv` is loaded when the process starts. Changing a rule means editing the file and restarting every API process. There is no audit of who changed a rule. The check itself is local and cheap, which is fine. The distribution of the file is the limit.

Load the policy from a store the instances share, and reload it without a full redeploy. Log policy changes the same way you would log a role change.

## Security edges that are fine for a demo

- CORS allows every origin (`allow_origins=["*"]` with credentials). A browser on any site can call the API if the user has a token.
- `/metrics` and `/health` are public. Counts and the breaker state are visible to anyone who can reach the port.
- Login has no rate limit. Password guesses are limited only by how fast the client can send them.
- Staff passwords live in `.env` and are seeded when the email is new. They are not rotated by the app.
- There is no audit table. An admin price change or role change is not a row you can review later.

Lock CORS to the real front-end origins. Put metrics on a private port. Rate-limit login and checkout. Write an audit row for catalog and role changes.

## Logging stops at the process

Each request logs one JSON line and sets `X-Request-ID`. That is enough to grep one container. It does not ship logs anywhere, does not trace the gateway call as a child of the request, and does not keep the id once the process is gone. Background work does not reliably carry the same id into a later worker.

Send logs to one place, and pass the request id into the gateway call and the notification job.

## Tests do not describe production

HTTP tests use a separate Postgres database named `shopping_test` on the same server as the app. They do not wipe the shopping database. If `DATABASE_URL` already starts with `sqlite`, those tests use `test_ecommerce.db` instead. There is no load test, no test that two checkouts race, and coverage is a report rather than a bar the build must pass. The suite is split between fakes and HTTP, which is the right shape, and it is still a small suite.

Add a test where two checkouts race for the last unit. Keep the fakes for the gateway. Add a threshold so a large drop in coverage fails the run.

## What to do first if this had to grow

1. Versioned migrations, and stop changing tables inside app startup.
2. Pagination on products, search, and orders.
3. A checkout idempotency key, and a job that finishes or releases `PENDING` orders.
4. More than one API process, a Postgres health check, and a shared place for the circuit breaker and metrics.
5. A queue for notifications, refresh-token storage, and a required `JWT_SECRET`.
6. Postgres in CI for the stock lock and the migrations.

The layering (router, service, repository, model) can stay. The limits above are about running more than one copy of that app, and about work that must survive a restart.
