# Limits, and easy mistakes

This API is a week 3 case study: one FastAPI process, one Postgres database, and a fake payment and email process. It is enough for a demo and an interview. It is not a shop that can take a sale, many servers, or a catalog of hundreds of thousands of products.

`limit.md` is an older note. Parts of it are no longer true. This file matches the code as it runs now.

---

## What production would add

| This project | A production shop |
| --- | --- |
| One Uvicorn process with `--reload` | Several API processes behind a load balancer, without reload |
| One Postgres, no pool size set, no replica | A pool sized for those processes, and replicas for catalog reads |
| `create_all` on startup | Versioned migrations (Alembic) that run before traffic |
| Cart does not hold stock | A short reservation that expires |
| Two checkout clicks make two orders | A client idempotency key, and the second click returns the first order |
| Circuit breaker and `/metrics` live in memory | A shared breaker, and metrics a scraper can store |
| Email is a `BackgroundTasks` job in this process | A queue and a separate worker, with retries that survive a restart |
| JWTs are not stored | Refresh tokens stored hashed, so logout and password change can revoke them |
| Policy is a CSV read at startup | A shared policy that reloads without restarting every box |
| CORS allows every origin | CORS locked to the real front end |
| Login has no rate limit | A limit on login and checkout guesses |
| Lists return every row | Pages, and search outside Postgres when the catalog is large |
| Tests do not race two checkouts | A test that two buyers cannot take the last unit, and a coverage bar in CI |

The layering can stay: router, service, repository, model. The gaps are about more than one copy of the app, and about work that must survive a restart.

---

## Logic limits that are real

**The cart does not reserve stock.** Adding an item only writes a line. Stock drops when checkout commits. Two people can both have the last unit in the cart. The loser is told at checkout, because checkout locks the product row with `FOR UPDATE`.

**A failed charge gives the stock back.** There is no cancel route and no job that later frees a stuck order. If the process dies after the commit and before the charge answer is saved, the order can sit on `PENDING` / `PENDING_PAYMENT` with the stock still reduced.

**Two clicks on checkout are two orders.** The idempotency key is the order number, and that number is new for each checkout. The fake API will not charge that same number twice. It will not stop a second checkout from creating `ORD-000002`. This app does not store the client's key.

**Retry of a paid order does not charge again. Retry of a failed order does reserve stock again.** The failure already returned the units. If the second charge fails, they are returned again.

**The circuit breaker is a variable in this process.** It starts closed. Five gateway errors open it for 30 seconds. A restart clears it. A second API container would have its own count. A decline does not count. Provider `fail` is HTTP 503, so it does count. Local `PAYMENT_FORCE=fail` is a decline, so it does not.

**Email can vanish.** The notice runs after the response, in the same process. If the process stops, the notice is gone. A failed notice is only a log line. The order is left as it is. There is no outbox table and no second worker.

**Delete hides a product.** `DELETE /api/admin/products/{id}` sets `is_active` to false. The row stays so old order lines still have a product. The shop list and the cart refuse it.

**Tokens cannot be revoked.** Access lasts 60 minutes. Refresh lasts 7 days. Nothing is saved server-side. A stolen access token works until `exp`. Logout does not exist. The role inside the token is ignored; each request loads `Users.Role`. A role change applies on the next call. The stolen token still works until it expires.

If `JWT_SECRET` is missing, the code uses `change-this-shopping-secret-key-32b`. Anyone who knows that string can mint tokens. The checked-in `.env` still has that same value.

**The policy is a file.** Editing `policy.csv` does nothing until every API process restarts. There is no record of who changed a rule.

**Schema changes are a new database.** `create_all` creates missing tables. It does not add a column to a table that already exists. The intended reset is `docker compose down -v`. That deletes the Postgres volume, including orders and users you created in the demo.

**Seed does not repair old rows.** If Rudraksh already exists, a later boot does not reset the password or the role. Demo passwords are in `app/db/seed.py`, not in `.env`.

**Lists are the whole table.** Products, search, order history, admin orders, and the audit log return every row. Ten products is fine. A large catalog is a large query and a large JSON body.

**Security that is fine for a class demo.** CORS is `allow_origins=["*"]` with credentials. `/health`, `/health/db`, and `/metrics` need no token. Login has no lockout. `/metrics` is a small in-memory report, not Prometheus.

**Tests are a small suite.** They use `shopping_test`, not the `shopping` database. They do not fire two checkouts at the last unit. Coverage is a report. `.coveragerc` does not fail the build. Ruff checks style. It does not prove the shop is correct.

**The fake API forgets charges on restart.** Paid references live in a dict in that process. `slow` sleeps 10 seconds inside that process. The shop's timeout is 2 seconds, so a shop checkout in `slow` mode fails and returns the stock. Calling `/payments/charge` yourself with a long wait still gets `PAID`.

---

## Mistakes that are easy to make

**"The role and the policy are the same thing."**
The role is the label on the user: `CUSTOMER`, `ADMIN`, `SUPPORT`. The policy is the list of what that label may do. Support can read every order. Support cannot edit products. That split is in `policy.csv`.

**"Support is a junior admin."**
Support has no cart, no catalog, and no audit log. `GET /api/admin/orders` works for support because that route asks for `order:read:any`, not for `catalog:manage`.

**"A customer can open someone else's orders with a user id in the path."**
That route is gone. The customer uses `GET /api/orders/me`. Admin and support use `GET /api/admin/orders`. An admin still cannot open another user's cart. The cart rule is "own cart only," including for admin.

**"Adding to the cart reduces stock."**
Stock changes at checkout. The cart only checks that the quantity is not already above the current stock.

**"A failed payment keeps the stock reduced."**
That was the older behavior. Now `PAYMENT_FAILED` adds the quantities back. The order row stays.

**"Retry just calls the gateway again."**
On a failed order, retry locks the products and takes the stock again before the charge. On a paid order, retry returns the same order and does not charge.

**"The idempotency key stops a double click."**
It stops a second charge of the same order number. A second checkout click is a new order number, a new stock drop, and a new charge.

**"Provider `fail` is a card decline."**
`PUT /mode/fail` returns 503. The shop retries that, and those failures can open the circuit breaker. A decline is `PAYMENT_FORCE=fail` when `PAYMENT_API_URL` is empty, or an HTTP 402. A decline is not retried and does not open the breaker.

**"`slow` means checkout waits 10 seconds and then succeeds."**
The fake API does wait 10 seconds. Checkout gives up at 2 seconds, retries, then saves `PAYMENT_FAILED` and puts the stock back.

**"A failed email fails the order."**
The notice runs after the response. If it fails, the log says `order_notification_failed`. `payment_status` stays what the charge already decided.

**"The circuit breaker is in Postgres and survives a restart."**
It is a Python object. Restart the API and the count is zero. `/metrics` is the same kind of memory.

**"Checkout being async means every route is async."**
Checkout, payment retry, category list, and the database health check await. Login, cart, product search, and admin writes are normal functions. Argon2 stays synchronous because it is CPU work, not waiting on the network.

**"`run_sync` means the database is still blocking the event loop the whole time."**
The charge is the awaited HTTP call. The stock lock stays a normal transaction because it needs one commit and `FOR UPDATE`.

**"Delete removes the product."**
The row remains with `is_active` false. The public product URL returns 404. An admin can still see it in `GET /api/admin/products`.

**"Register can create an admin if I send the role."**
The body refuses extra fields. `"role": "ADMIN"` is 422. Only an admin can change a role, and not their own. The last admin cannot be demoted.

**"Login is by username."**
Login is the email. The Swagger token box also sends that email in the username field. The column is `Users.Email`.

**"Argon2 broke the old passwords."**
New hashes start with `$argon2`. A stored `salt$hex` hash still verifies until that user is created again.

**"`create_all` updates an old database, and migrate.py does that too."**
Startup only calls `create_all`. That creates tables that are missing. It does not add columns to tables that already exist. There is no migrate step in startup. `docker compose down -v` is how this project gets a new schema.

**"Seed resets Rudraksh's password."**
An email that is already there is skipped. `docker compose exec api python -m app.db.seed` prints `Seeded.` and leaves existing users alone. The command needs the service name `api`.

**"There is one database, so tests wipe the shop."**
The app uses `shopping`. Tests use `shopping_test` on the same Postgres, unless `DATABASE_URL` starts with `sqlite`, in which case they use `test_ecommerce.db`.

**"All 37 tests are integration tests."**
Twenty call a function or the fake API and do not use the shopping database. Seventeen are marked `integration` and do use it.

**"The app will not start without `.coveragerc`."**
That file only changes a coverage report. Plain `pytest` never reads it. Ruff is the same: the app runs if you never call Ruff.

**"Payment and email are two servers."**
One process on port 9000. Charges are `POST /payments/charge`. Email is `POST /notify`. The Swagger page has a Notifications section and a Charges section.

**"The Docker attach config talks to SQLite."**
`Attach to API in Docker` connects to port 5678 and the Postgres in Compose. The SQLite entries are only for a process you start on your own machine.

**"`GET /health` means Postgres is ready."**
`/health` means this process answered. `/health/db` runs `SELECT 1`. Neither one asks the fake API if it is up. Compose does wait for `pg_isready` before it starts the API.
