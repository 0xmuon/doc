# API routes this shop screen does not call

The React app talks to the shopping API at `http://localhost:8000`. Start that API first (`docker compose up`), then from the `frontend` folder run `npm run dev`.

These routes are the ones the screens use, so a customer can register, browse, fill a cart, and place an order:

| Method | Path | Screen |
| --- | --- | --- |
| POST | `/api/users/register` | Register |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Restore the logged-in user, and the profile page |
| GET | `/api/categories` | Category dropdown on the product list |
| GET | `/api/products` | Product list |
| GET | `/api/products/search` | Search by name or category |
| GET | `/api/products/{product_id}` | Product details |
| POST | `/api/cart/add` | Add to cart from the product list, product page, or when plus raises a quantity from zero |
| GET | `/api/cart/{user_id}` | Cart, and the in-cart count on the product list and product page |
| PUT | `/api/cart/update/{cart_item_id}` | Change quantity from the cart, product list, or product page |
| DELETE | `/api/cart/remove/{cart_item_id}` | Remove a line, including when minus takes the quantity to zero |
| POST | `/api/orders/checkout` | Checkout. Payment method is `CARD` (Credit Card) or `COD` (Cash on Delivery) |
| GET | `/api/orders/me` | Order history, and placed orders on the profile page |
| GET | `/api/orders/details/{order_id}` | Order details |
| POST | `/api/payments/process` | Pay again, only when `payment_status` is `FAILED` |

The cart total and item count are added up in the browser from the cart lines. The API has no cart-summary route.

Register also sends `mobile` (10 digits). The week 4 form lists name, email, and password. This API rejects a registration that has no mobile, so the field is on the form so an account can be created and an order can be placed.

## Not used by the frontend

These exist on port 8000 and are not called by any screen:

| Method | Path | Why it is unused |
| --- | --- | --- |
| POST | `/api/users/login` | Login uses `/api/auth/login` instead. Same check. |
| POST | `/api/auth/refresh` | Not a screen. `api/client.js` calls it once after a 401 and retries the original request. |
| POST | `/api/auth/token` | Hidden Swagger login. The screen does not use it. |
| GET | `/health` | Process check. Not a shop screen. |
| GET | `/health/db` | Database check. Not a shop screen. |
| GET | `/metrics` | Counters. Not a shop screen. |
| POST | `/api/admin/categories` | Admin catalog. No admin screen. |
| PUT | `/api/admin/categories/{category_id}` | Admin catalog. |
| GET | `/api/admin/products` | Admin product list, including inactive rows. |
| POST | `/api/admin/products` | Admin create product. |
| PUT | `/api/admin/products/{product_id}` | Admin update product. |
| DELETE | `/api/admin/products/{product_id}` | Deactivate a product. |
| GET | `/api/admin/orders` | Every order, for admin and support. The screen shows only the logged-in user's orders. |
| GET | `/api/admin/audit-logs` | Admin audit log. |
| PATCH | `/api/admin/users/{user_id}/role` | Role change. |
| POST | `/api/notifications/send` | Email is already sent by the API during checkout. |

Checkout does not offer `UPI` or `NET_BANKING`. The week 4 brief asks for Credit Card and Cash on Delivery only. The checkout route still accepts those other methods if something else calls it.

The fake payment and email API on port 9000 is not called by the browser. The shopping API on port 8000 calls it during checkout.
