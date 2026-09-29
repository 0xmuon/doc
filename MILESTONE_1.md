# Milestone 1 — JWT login and protected routes

Week 3 milestone 1 asks for JWT-based authentication and protected routes. This API does that and stops there. Roles, admin product APIs, payment retries, async work, and tests are later milestones.

Browse, register, and login stay public. Cart and orders need a bearer token, and the `user_id` in the path or body has to be the same person as the token.

---

## What changed from week 2

Week 2 login already checked the email and the stored password hash in the `Users` table. A wrong email and a wrong password both returned **401** `Invalid email or password`. Register still returns no token.

Milestone 1 adds one step after that check succeeds: the API signs a JWT and sends it back. Later cart and order calls must send that token.

Two login URLs share the same function:

| Method | Path | What it does |
| --- | --- | --- |
| POST | `/api/users/login` | Week 2 login. Now also returns the token. |
| POST | `/api/auth/login` | Same body, same response. This is the auth path from the week 3 case study. |

There is no refresh endpoint. The case study lists `POST /api/auth/refresh` as optional, and it was left out.

---

## The login flow

1. The client sends `email` and `password`.
2. The schema lowercases the email. Login does not enforce the 8-character password rule; register does.
3. `login_user` loads the row by email.
4. `verify_password` rebuilds the PBKDF2-HMAC-SHA256 hash with the stored salt and compares it. The stored value looks like `salt$hex`.
5. If the user is missing or the hash does not match, the response is **401** `Invalid email or password`. The two cases are the same message on purpose.
6. If the hash matches, `create_access_token` signs a JWT. The password is never put in the token.
7. The response is **200**:

```json
{
  "message": "Login successful",
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "user_id": 3,
    "name": "Rudra",
    "email": "rudra@example.com",
    "mobile": "9988776655"
  }
}
```

`UserResponse` has no password field, so the hash never leaves the database.

Register is still **201** with `message` and `user` only. The client has to log in to get a token.

---

## What is inside the token

`app/utils/security.py` builds the token with PyJWT and **HS256**.

| Claim | Value |
| --- | --- |
| `sub` | User id as a string. This is who the token belongs to. |
| `email` | Email at login time. The route still loads the user from the database by `sub`. |
| `exp` | UTC time when the token dies. Default is 60 minutes. |

The signature is made with `JWT_SECRET`. Anyone who does not have that secret cannot mint a token this API will accept. Changing the secret invalidates every token already issued.

Settings live in `.env` (see `.env.example`):

```
JWT_SECRET=change-this-shopping-secret-key-32b
JWT_EXPIRE_MINUTES=60
```

HS256 wants a secret of at least 32 characters, which is why the default is already that long. If the variables are missing, the code uses those same defaults.

---

## How a protected route decides

`app/utils/deps.py` is the gate. Cart and order routers attach `get_current_user` to the whole router, and each handler also asks for the current user. FastAPI runs that dependency once per request.

`HTTPBearer(auto_error=False)` is deliberate. With the default, a missing `Authorization` header becomes FastAPI's own **403**. This API wants **401** for "you are not logged in."

`get_current_user` does this:

1. No header, or the scheme is not `Bearer` → **401** `Valid token is required`.
2. `decode_access_token` checks the signature and `exp`. A bad signature, a tampered payload, or an expired token all become **401** `Invalid or expired token`.
3. `sub` must be an integer. If it is not, same **401**.
4. That id is loaded from `Users`. If the row is gone, same **401**. A token for a deleted user does not keep working.
5. The handler receives the `User` row.

Then `require_owner` compares `current_user.user_id` with the `user_id` in the path or body. They must match. If they do not, the response is **403** `You can only access your own cart` or `You can only access your own orders`. The service is not called, so this is not **404** `User not found`.

Order details are the one route with no `user_id` in the path. The handler loads the order, then checks `order.user_id` against the token. A missing order is still **404**. Someone else's order is **403**.

`GET /api/orders/me` skips the path id. It lists orders for `current.user_id` only.

---

## Which routes need the token

Public:

| Method | Path |
| --- | --- |
| POST | `/api/users/register` |
| POST | `/api/users/login` |
| POST | `/api/auth/login` |
| GET | `/api/categories` |
| GET | `/api/products` |
| GET | `/api/products/search` |
| GET | `/api/products/{product_id}` |

Token required. The `user_id` must match the token, except `GET /api/orders/me` and order details (those use the token, then the order's owner):

| Method | Path |
| --- | --- |
| GET | `/api/cart/{user_id}` |
| GET | `/api/cart/{user_id}/summary` |
| POST | `/api/cart/add` |
| PUT | `/api/cart/update/{user_id}/{product_id}` |
| DELETE | `/api/cart/remove/{user_id}/{product_id}` |
| POST | `/api/orders/checkout` |
| GET | `/api/orders/me` |
| GET | `/api/orders/{user_id}` |
| GET | `/api/orders/details/{order_id}` |

Cart and checkout behavior is unchanged once the caller is allowed through. An open cart is still one basket per user, `cart_id` still starts at 1 for each user, and checkout still closes that basket. The token only decides who is allowed to touch it.

---

## Status codes for this milestone

| Code | When |
| --- | --- |
| **200** | Login succeeded, or a protected read/update/delete succeeded. |
| **201** | Register, add to cart, or checkout succeeded. |
| **401** | Bad login, missing token, wrong scheme, bad signature, expired token, or the token's user no longer exists. |
| **403** | Token is valid, but it is for a different user than the cart, checkout body, order history path, or order being viewed. |
| **422** | Body failed schema checks (bad email, short password on register, mobile not 10 digits). |

**401** means "prove who you are." **403** means "we know who you are, and this is not yours."

---

## Call it

Header on every cart or order request:

```
Authorization: Bearer <access_token>
```

In Swagger (`http://127.0.0.1:8000/docs`), open **Authorize** and paste the token only. Do not type the word `Bearer`. Swagger adds that prefix.

Login:

```http
POST /api/auth/login
Content-Type: application/json

{"email": "you@example.com", "password": "secret123"}
```

`POST /api/users/login` accepts the same JSON.

Own cart:

```http
GET /api/cart/3
Authorization: Bearer <token for user 3>
```

Another user's cart with that same token:

```http
GET /api/cart/4
Authorization: Bearer <token for user 3>
```

That returns **403**, not the other cart.

`POST /api/cart/add` and `POST /api/orders/checkout` still send `user_id` in the JSON. That id must equal the token's user. Sending `99999` with your token is **403** before the cart service runs.

---

## Where the code lives

| File | Job |
| --- | --- |
| `app/utils/security.py` | Read `JWT_SECRET` and expiry. Create and decode the token. |
| `app/utils/deps.py` | `get_current_user` and `require_owner`. |
| `app/utils/exceptions.py` | `UnauthorizedException` is 401. `ForbiddenException` is 403. `main.py` returns both as `{"detail": "..."}`. |
| `app/services/user_service.py` | Hash check, then `create_access_token`. |
| `app/schemas/user_schema.py` | `LoginResponse` includes `access_token` and `token_type`. |
| `app/routers/user_router.py` | `POST /api/users/login`. |
| `app/routers/auth_router.py` | `POST /api/auth/login`. |
| `app/routers/cart_router.py` | Every cart route requires the token and the matching user. |
| `app/routers/order_router.py` | Every order route requires the token. History and checkout also require the matching user. |
| `requirements.txt` | `PyJWT`, unpinned, same style as the other dependencies. |
| `.env.example` | `JWT_SECRET` and `JWT_EXPIRE_MINUTES`. |

Request path is still router → service → repository. The token check sits in the router dependency, before the service.

---

## What this milestone does not do

- No `Role` column and no Admin or Support checks. Any registered user can use their own cart and orders. That is milestone 2.
- No `POST /api/auth/refresh`. Log in again after 60 minutes.
- No token on register.
- Product and category reads stay public.
- The password hash algorithm did not change. JWT is only the session proof after that check.
