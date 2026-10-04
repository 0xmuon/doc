# Milestone 1 — JWT login and protected routes

## Run this copy

This folder is the app as it stood at milestone 1, including `app/`, the Dockerfile, and Compose. It does not import the project root.

```powershell
cd milestones\milestone_1
docker compose up --build
```

Open `http://127.0.0.1:8011/docs`. Postgres on your machine is `localhost:5441` (user `shop`, password `shop`, database `shopping`). The project root stays on port 8000, so this copy can run beside it.

## Concepts used

**Cart line identity.** Week 2’s `CartItems` table has `CartItemID` as an auto-generated primary key, plus `UserID`, `ProductID`, and `Quantity`. There is no `Carts` table and no `CartID` on `Orders`. `PUT /api/cart/update/{cart_item_id}` and `DELETE /api/cart/remove/{cart_item_id}` use that id. Adding the same product again keeps the same `cart_item_id` and increases `Quantity`. Checkout copies the current price onto `OrderDetails`, reduces stock, and deletes the cart lines.

**JWT.** A JSON Web Token is a signed string the server can check without storing a session. Login signs it with HS256 using `JWT_SECRET`. The claims are `sub` (the user id), `email`, and `exp` (default 60 minutes). The password is never inside the token. Anyone who has the secret can forge a token, which is why the secret stays in `.env`.

**Bearer authentication.** The client sends `Authorization: Bearer <token>`. `HTTPBearer(auto_error=False)` lets this app return **401** when the header is missing. FastAPI’s default for a missing bearer header is **403**, which would mix “not logged in” with “logged in but not allowed.”

**Password hashing.** The stored value is `salt$hex` from PBKDF2-HMAC-SHA256. Login hashes the password the client sent and compares it. Unknown email and wrong password both return **401** `Invalid email or password`, so the response does not say which one failed.

**Authentication and the owner check.** This milestone checks who you are (the token) and that the `user_id` on the cart or order is that person (`require_owner`). It does not check a role. That comes in milestone 2.

**401 and 403.** **401** means the token is missing or not valid. **403** means the token is valid and the row belongs to someone else.

**Dependencies.** FastAPI runs `get_current_user` before the route function. The service never sees a request that has not already been tied to a `Users` row.

**Layers.** The request still goes router, then service, then repository, then the model. Pydantic checks the body before the service runs.

Week 3 milestone 1 is: implement JWT-based authentication and protected routes.

This folder stops at login and protected cart and order routes. Later milestones are the other folders.

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

In Swagger (`http://127.0.0.1:8011/docs`), Authorize, and paste the token only. Do not type the word `Bearer`.

## Who gets through

`app/utils/deps.py` uses `HTTPBearer(auto_error=False)` so a missing header is our **401**, not FastAPI's default **403**.

| Situation | Result |
| --- | --- |
| No header, or the scheme is not Bearer | **401** `Valid token is required` |
| Bad signature, expired token, bad `sub`, or the user row is gone | **401** `Invalid or expired token` |
| Token is valid, but the `user_id` or the `cart_item_id` belongs to someone else | **403** `You can only access your own cart` or `You can only access your own orders` |
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
