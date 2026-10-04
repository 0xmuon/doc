# Milestone 1 — JWT login and protected routes

## Run this copy

This folder is the app as it stood at milestone 1, including `app/`, the Dockerfile, and Compose. It does not import the project root.

```powershell
cd milestones\milestone_1
docker compose up --build
```

Open `http://127.0.0.1:8011/docs`. Postgres on your machine is `localhost:5441` (user `shop`, password `shop`, database `shopping`). The project root stays on port 8000, so this copy can run beside it.


Week 3 milestone 1 is: implement JWT-based authentication and protected routes.

This folder stops at login and protected cart and order routes. Later milestones are the other folders. The week 3 sheet still says `cart_item_id`. This API uses a basket `cart_id` and a `product_id` on the line. That does not change here.

## What you get

Register stays public and returns no token. Login checks the email and the stored password hash, then returns a signed JWT.

Two URLs share one function:

| Method | Path |
| --- | --- |
| POST | `/api/users/login` |
| POST | `/api/auth/login` |

There is no refresh route. The case study lists `POST /api/auth/refresh` as optional.

Browse stays public: categories, products, search, and product details. Cart and orders require `Authorization: Bearer <token>`.

## Login

1. The body is `email` and `password`. The email is lowercased.
2. The user is loaded from `Users`. The password is checked with PBKDF2-HMAC-SHA256 against the stored `salt$hex`.
3. Unknown email and wrong password both return **401** `Invalid email or password`.
4. On a match, `create_access_token` signs an HS256 JWT. The password is never inside it.
5. The response is **200** with `message`, `access_token`, `token_type` `bearer`, and `user` (no password).

Claims: `sub` is the user id as a string, `email`, `exp` (default 60 minutes), and, from milestone 2 onward, `role`. Routes do not trust `role` inside the token. They load the `Users` row.

`JWT_SECRET` and `JWT_EXPIRE_MINUTES` come from `.env`. The default secret is already 32 characters because HS256 warns on a short key.

In Swagger (`http://127.0.0.1:8000/docs`), Authorize, and paste the token only. Do not type the word `Bearer`.

## Who gets through

`app/utils/deps.py` uses `HTTPBearer(auto_error=False)` so a missing header is our **401**, not FastAPI's default **403**.

| Situation | Result |
| --- | --- |
| No header, or the scheme is not Bearer | **401** `Valid token is required` |
| Bad signature, expired token, bad `sub`, or the user row is gone | **401** `Invalid or expired token` |
| Token is valid, but the `user_id` in the path or body is someone else | **403** `You can only access your own cart` or `You can only access your own orders` |
| Token user matches | The cart or order service runs |

`GET /api/orders/me` uses the token user and has no path id. Order details load the order first: missing order is **404**, someone else's order is **403** (milestone 2 lets admin and support through).

## Files

| File | Role |
| --- | --- |
| `app/utils/security.py` | Create and decode the token |
| `app/utils/deps.py` | `get_current_user`, `require_owner` |
| `app/utils/exceptions.py` | 401 and 403 |
| `app/services/user_service.py` | Hash check, then the token |
| `app/schemas/user_schema.py` | `LoginResponse` |
| `app/routers/user_router.py` | `/api/users/login` |
| `app/routers/auth_router.py` | `/api/auth/login` |
| `app/routers/cart_router.py` | Token on every cart route |
| `app/routers/order_router.py` | Token on every order route |

The request path is still router, then service, then repository. The token check happens in the dependency, before the service.

## Left for later milestones

Milestone 1 does not know Customer, Admin, or Support. Any logged-in user could call any cart or order route as themselves. Milestone 2 adds the role check in front of that owner check.
