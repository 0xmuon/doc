# Milestone 6 — tests, coverage, and git

## Run this copy

This folder is the app as it stood at milestone 6, including `app/`, the Dockerfile, and Compose. It does not import the project root.

```powershell
cd milestones\milestone_6
docker compose up --build
```

Open `http://127.0.0.1:8016/docs`. Postgres on your machine is `localhost:5446` (user `shop`, password `shop`, database `shopping`). The project root stays on port 8000, so this copy can run beside it.


Week 3 milestone 6 is: add unit testing, coverage validation, and finalize Git-based delivery.

The tests exercise the running design: JWT, roles, the admin catalog, payment fail-then-retry, the async category list, and the background notification response. They use a sqlite file so the sync pool and the async pool see the same rows. They do not wipe the Docker Postgres volume.

## How to run

From this folder, with the packages in `requirements.txt` installed:

```powershell
python -m pytest tests -q --cov=app --cov-report=term-missing
```

The last run of that command was **9 passed**, about **83%** line coverage of `app/`. Coverage is a report, not a gate that fails the build. The missing lines are mostly the HTTP branch of the gateway (used when `PAYMENT_API_URL` is set) and a few validation branches.

`tests/conftest.py` points `DATABASE_URL` at `.pytest_shopping.db` before the app is imported, and sets the staff emails and `PAYMENT_FORCE=ok`. That file is gitignored.

## What is covered

| File | What it locks |
| --- | --- |
| `tests/test_permissions.py` | Customer cannot manage the catalog. An unknown role is denied. Support can read another user's order. A customer cannot |
| `tests/test_retry.py` | The third try can succeed. Two failures raise `GatewayError` |
| `tests/test_api.py` | Public catalog is 10 products and 4 categories. Register with a `role` field is **422**. Login returns `CUSTOMER`. Cart without a token is **401**. Another user's cart is **403**. Support can read orders and cannot create a category. Admin creates a category, rejects a duplicate name, and deactivates a product so the public GET is **404**. Checkout with `PAYMENT_FORCE=fail` is **201** and `FAILED`. Process payment moves it to `PAID` and a second call stays `PAID`. Notification returns `Notification queued`. Admin can list orders. A role change to support blocks the next cart add with the same account |

`GET /api/categories` in the first test is the async route. The response header `X-Request-ID` is the milestone 5 log id.

## Git

The repository already ignores `.env`, `__pycache__`, `.venv`, the pytest database, and coverage output. Do not commit `.env`. The sample variables live in `.env.example`.

This milestone does not create a commit by itself. When you want the week 3 work in git:

```powershell
git status
git add app tests requirements.txt .env.example .gitignore milestones
git commit -m "Add week 3 auth, admin, payments, async reads, and tests."
```

Leave `week3.pdf` out if you do not want the brief in the repository. Do not `git add .env`.

A normal delivery from here is one branch for this week, the commit above, and a pull request if the remote is the place the case study is reviewed. The tests above are what you run before that push.

## What the six milestones are, together

Each folder under `milestones/` is its own app and its own database volume. The project root is the same code as milestone 6, on port 8000.

| Folder | In that copy |
| --- | --- |
| `milestones/milestone_1` | JWT on both login routes. Cart and orders require it |
| `milestones/milestone_2` | `Role` and the permission map. Support reads orders. Admin changes roles |
| `milestones/milestone_3` | Admin category and product routes, deactivate, all orders |
| `milestones/milestone_4` | Payment after the order commit, retry, `payment_status` |
| `milestones/milestone_5` | Async categories, background notification, JSON request logs |
| `milestones/milestone_6` | This test run and the git notes above |

Cart ids still start at 1 for each user. Models stay in `app/models`. The database in Docker is still Postgres.
