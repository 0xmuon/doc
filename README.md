# Online Shopping Application API

Functional backend for the user module of an online shopping application: register, login, browse and search products, manage a cart, and place orders.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL 17

## Run with PostgreSQL

```powershell
docker compose up --build
```

The API is on port 8000. Postgres is published on localhost port 5433 (user `shop`, password `shop`, database `shopping`). Inside Compose the API uses host `db` and port 5432.

To run the API on your machine against that same database, start only Postgres, point `DATABASE_URL` at `localhost:5433`, then start the app:

```powershell
docker compose up db -d
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

In `.env`, change the host from `db` to `localhost` and the port from `5432` to `5433` before that last command. `docker compose up --build` can keep host `db`.

Open `http://127.0.0.1:8000/docs` for Swagger.

Passwords are stored as salted hashes. Login checks the email and password against the Users table, then returns a JWT. Cart and order routes need that token in the `Authorization: Bearer` header. The `user_id` in the path or body must be the same user as the token. Product browse stays open. Sample catalog data is inserted on startup when the database is empty.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/users/register` | Register a user |
| POST | `/api/users/login` | Login and receive a JWT |
| POST | `/api/auth/login` | Same login, auth path from the case study |
| GET | `/api/categories` | List categories |
| GET | `/api/products` | List products |
| GET | `/api/products/{id}` | Product details |
| GET | `/api/products/search?name=&category=` | Search by name and/or category |
| GET | `/api/cart/{user_id}` | View cart (token required) |
| POST | `/api/cart/add` | Add an item (token required) |
| PUT | `/api/cart/update/{user_id}/{product_id}` | Set quantity on the open cart (token required) |
| DELETE | `/api/cart/remove/{user_id}/{product_id}` | Remove a product from the open cart (token required) |
| GET | `/api/cart/{user_id}/summary` | Cart totals (token required) |
| POST | `/api/orders/checkout` | Place an order (token required) |
| GET | `/api/orders/me` | My order history (token required) |
| GET | `/api/orders/{user_id}` | Order history for that user (token required) |
| GET | `/api/orders/details/{order_id}` | Order details (token required) |

Payment methods: `COD`, `CARD`, `UPI`, `NET_BANKING`.

Checkout checks that the open cart is not empty, that each quantity is still in stock, calculates the total from current prices, stores those prices on the order lines, reduces stock, and marks that cart as ordered. The next add opens a new cart for the same user, numbered 2, then 3, and so on. Each user's first cart is `cart_id` 1.
