# What each frontend file does

The browser talks only to `/api`. Vite proxies that to FastAPI on port 8000. Port 9000 is called by the Python API, never by these files.

## Startup

### `index.html`

One empty `<div id="root">`. The title is ABC Shop. There is no page markup here.

### `src/main.jsx`

`createRoot` renders `<App />` inside `<StrictMode>` and imports `index.css`. StrictMode is why development effects run twice. See `FRONTEND_INTERVIEW.md`.

### `src/index.css`

`@import "tailwindcss"` plus `body { margin: 0 }`. This is the only stylesheet. Component files put Tailwind class names on the elements.

### `src/App.jsx`

Wraps the tree: `AuthProvider`, then `CartProvider`, then `BrowserRouter`. The route table is here. `Layout` is the parent route, so every page gets the header and footer through `<Outlet />`. Cart, checkout, orders, order details, and profile sit inside `ProtectedRoute`. `*` is `NotFoundPage`.

### `vite.config.js`

Plugins are React and Tailwind. `server.proxy` sends `/api` to `VITE_API_PROXY_TARGET` or `http://localhost:8000`.

## Layout

### `src/components/layout/Layout.jsx`

A column at least as tall as the screen: `Header`, `<main><Outlet /></main>`, `Footer`. No API calls.

### `src/components/layout/Header.jsx`

The top bar. Brand links to `/home`. Renders `Menu`. If `useAuth().user` exists, shows the name, a profile link to `/profile`, and Log out (`logout()` clears local storage only). If not, shows the profile icon, Login, and Register, all linking to `/login` or `/register`.

### `src/components/layout/Menu.jsx`

The navbar: Home, Products, Cart, Orders. `NavLink` underlines the active item. Home is also active on `/`. Cart text includes ` (${itemCount})` when `useCart().itemCount` is above 0. No API call of its own. The count comes from `CartContext`.

### `src/components/layout/Footer.jsx`

Shop links go to `/home` or `/products`. Help Center, Returns, Shipping, and Contact Us are text, not links. Email is `mailto:support@abcshop.example`. Phone is `tel:+1234567890`. Copyright is “© 2026 ABC Shop. All Rights Reserved.”

## Login state

### `src/context/auth-context.js`

Creates the context. `useAuth()` reads it. `safeReturnPath` accepts only a string that starts with one `/`, otherwise `/products`. This blocks an open redirect such as `//evil.example`.

### `src/context/AuthContext.jsx`

Holds the session. Storage key `abcshop_session` is `{ token, refreshToken, user }`. `writeSession` also copies the tokens into `tokenStore` (`abcshop.accessToken`, `abcshop.refreshToken`).

On mount, if a token exists, `fetchCurrentUser` runs. Success refreshes the stored user. Failure clears the session. `ready` starts true when there is no token, and becomes true after the `/api/auth/me` attempt when there is one.

`login` calls `loginUser`. `register` calls `registerUser` and does not log the user in. `logout` only clears the browser.

When `client.js` refreshes tokens, `setTokensRefreshedHandler` updates the session. When refresh fails, `setSessionExpiredHandler` logs the user out.

Backend: `POST /api/auth/login` → `user_service.login_user`. `POST /api/users/register` → `user_router.register`. `GET /api/auth/me` → `auth_router.auth_me`.

## Cart state

### `src/context/cart-context.js`

Creates the context. `useCart()` reads it.

### `src/context/CartContext.jsx`

After auth is `ready`, loads the cart. Logged out, the visible cart is empty and no request is sent. Logged in, `GET /api/cart/{userId}` → `cart_router.view_cart` → `cart_service.get_cart`. A failed load becomes `{ items: [] }`.

The value passed down includes `items`, `itemCount` (sum of quantities), `overStock` (any line above `available_quantity` or above `MAX_QUANTITY_PER_ITEM`), `refreshCart`, and `setCart`. `refreshCart` is what pages call after an add, update, remove, checkout, or return to cart.

## API client

### `src/api/client.js`

`api()` is the only `fetch` used by the screens, except the refresh call inside this file. It sends `Authorization: Bearer` when a token exists. A non-OK response becomes `ApiError` with `status`, `fieldErrors`, and `requestId`. The message appends `(ref: …)` from `X-Request-ID` or the body `request_id`.

On 401, once, it posts `{ refresh_token }` to `POST /api/auth/refresh` → `user_service.refresh_session`. Parallel 401s share that one request. The original call is retried with the new access token and will not refresh a second time. Failure clears both tokens and runs the session-expired handler.

### `src/api/authApi.js`

`loginUser` → `POST /api/auth/login` with JSON `{ email, password }`. `registerUser` → `POST /api/users/register` with the payload, which includes `mobile`. `fetchCurrentUser` → `GET /api/auth/me`.

### `src/api/productApi.js`

`fetchCategories` → `GET /api/categories` → `product_service.list_categories_async`. `fetchProducts` → `GET /api/products` → `list_products` (active only). `searchProducts` → `GET /api/products/search` → `product_repository.search` (`ILIKE` on product name, exact category name). `fetchProduct` → `GET /api/products/{id}` → `get_product` (404 if missing or inactive).

### `src/api/cartApi.js`

`fetchCart` → `GET /api/cart/{userId}`. `addCartItem` → `POST /api/cart/add` with `{ user_id, product_id, quantity }`. `updateCartItem` → `PUT /api/cart/update/{id}` with `{ quantity }`. `removeCartItem` → `DELETE /api/cart/remove/{id}`. All four land in `cart_router` and then `cart_service`.

### `src/api/orderApi.js`

`placeOrder` → `POST /api/orders/checkout` → `order_service.checkout`. `fetchMyOrders` → `GET /api/orders/me` → `list_orders`. `fetchOrder` → `GET /api/orders/details/{id}` → `get_order`. `retryPayment` → `POST /api/payments/process` → `order_service.retry_payment`, then a background notice. `returnOrderToCart` → `POST /api/orders/{id}/return-to-cart` → `order_service.return_to_cart`.

## Hooks and small helpers

### `src/hooks/useForm.js`

Register and login. Holds `values`, `touched`, and `submitted`. `validate(values)` returns a message per field. `isValid` is true when every message is empty. `visibleError` shows a message only after blur or after `touchAll` on submit. `reset` restores the initial values.

### `src/hooks/useDebouncedValue.js`

Returns the value from 300 ms ago. Each change clears the previous timer. `ProductsPage` uses it so search does not call the API on every keystroke.

### `src/utils/validate.js`

`validateName`: required, at least 6 characters, letters with single spaces (`/^[A-Za-z]+( [A-Za-z]+)*$/`). `validateEmail`. `validatePassword`: 8 characters, upper, lower, digit, special. `validateLoginPassword`: non-empty only. `validateMobile`: exactly 10 digits. `validateQuantity`: required, positive whole number, not above stock, not above `VITE_MAX_QUANTITY_PER_ITEM` (default 10).

### `src/utils/validate.test.js`

Vitest. Covers the quantity cap of 10, a double space and a digit in the name, and email. `npm test` runs this file only.

### `src/utils/money.js`

`inr(amount)` returns `INR 799` for a whole number and two decimals when there are paise. No rupee sign.

### `src/utils/cartQuantity.js`

`setCartQuantity` refuses a quantity above stock or above the cap of 10. Under 1 deletes the line. No line means add. An existing line means update. Callers then `refreshCart`.

### `src/utils/statusLabels.js`

Turns `order_status` and `payment_status` into pill text. `CONFIRMED` → Confirmed. `PAYMENT_FAILED` → Payment Failed. Anything else on the order → Pending Payment. Then `PAID` adds Paid, `FAILED` adds Payment Failed if it is not already there, and `PENDING` adds Pending Payment if it is not already there. A paid card order is Confirmed and Paid. Cash on delivery is Confirmed and Pending Payment. A failed card is Payment Failed once.

## Shared components

### `src/components/common/ProtectedRoute.jsx`

If `ready` is false, shows “Checking your session...”. If there is no user, `<Navigate to="/login">` with `state.from` set to the path they wanted. Otherwise renders `children`.

### `src/components/common/StatusBadge.jsx`

A colored pill. Confirmed and Paid are blue. Pending Payment is yellow. Payment Failed is red. The label text is chosen by `statusLabels`, not by this file.

### `src/components/products/SearchBar.jsx`

Controlled search input. Placeholder “Search products by name or category...”. `maxLength` 100. It does not call the API. `ProductsPage` does, after the debounce.

### `src/components/products/ProductCard.jsx`

Shows image or “No image”, name (link to `/products/{id}`), category or “Uncategorised”, description or “No description available.”, `inr(price)`, “In cart: N”. Add to Cart calls `onChange(product, cartQuantity + 1)` and is disabled at stock or at 10, or while `busy`. Otherwise the card says “Out of Stock”. `message` is the stock error for this product.

### `src/components/orders/OrderListItem.jsx`

One history row: number, date, optional payment-method label, total, pills from `statusLabels`, and View details linking to `/orders/{id}`. Profile passes “Credit Card” or “Cash on Delivery” as `detail`. The orders page does not.

## Pages

### `src/pages/HomePage.jsx`

Static welcome and three links: products, cart, orders, plus Login and Register. No API. Cart and orders still pass through `ProtectedRoute` when opened.

### `src/pages/RegisterPage.jsx`

Form through `useForm`. Submit trims name, email, and mobile, then `register()`. Duplicate email (status 409 or a message that mentions email) is shown under the email field as “This email is already registered”. Success goes to login with “Registration successful. Please log in.” Reset clears the form and the server messages. The submit button is disabled until valid and while `busy`.

### `src/pages/LoginPage.jsx`

Email and non-empty password. Shows `location.state.message` (the register success line, or “Please log in to add items to your cart.”) until a server error replaces it. A 401 is “Invalid email or password”. Success uses `safeReturnPath(location.state.from)`.

### `src/pages/ProductsPage.jsx`

Loads categories once. Loads products when the debounced name or the category dropdown changes. `loadProducts` merges a typed category name in the browser because `GET /api/products/search` only applies `ILIKE` to `product_name`. Out-of-stock rows sort last. Add to Cart for a guest goes to login. A logged-in add uses `setCartQuantity` then `refreshCart`. `pendingRef` blocks a second add. A stale response is ignored.

### `src/pages/ProductDetailsPage.jsx`

`useParams().productId`. `GET /api/products/{id}`. A 404 is “Product not found.” Other errors show `err.message`. The page shows the previous product as “Loading product...” until the new id has loaded (`loadedId === productId`), so a slow response cannot flash the wrong product.

Qty is how many to add this click. Validation checks the typed value and `inCart + typed` against stock and the cap of 10 before it checks login. Guest redirect uses the current path. Success stays on this page, resets Qty to 1, and refreshes the cart. The button is disabled when the line is already at stock or at 10.

### `src/pages/CartPage.jsx`

Lists `useCart().items`. `CartQuantityInput` keeps its own text, validates on change, and saves 500 ms later with `updateCartItem` only when the value is valid and different. It does not reset the text while the input is focused. Remove uses `removeCartItem`. Checkout links to `/checkout` and is disabled when the cart is empty or `overStock`. Empty cart copy is “Your cart is empty.”

### `src/pages/CheckoutPage.jsx`

Requires the cart from context. Payment `<select>` is only `CARD` (Credit Card) and `COD` (Cash on Delivery). Submit posts `{ user_id, payment_method }`. Then `refreshCart`. Navigation is always `/orders/{order_id}`. `state.justPlaced` is set when `payment_status` is not `FAILED`. The button is disabled when the cart is empty, any line is over stock or over 10, or `busy`.

Backend split: `order_service._reserve` writes the order and clears the cart. `COD` stops in `_confirm_cod`. `CARD` continues to `payment_gateway.charge_order` and the provider on port 9000. The notice is queued in `order_router.checkout`.

### `src/pages/OrdersPage.jsx`

After `ready`, `GET /api/orders/me`. Renders `OrderListItem` for each row. Zero rows: “No orders found.” This list includes failed and pending orders. Profile does not.

### `src/pages/OrderDetailsPage.jsx`

`GET /api/orders/details/{orderId}`. 403 and 404 have their own sentences. Shows thank you only when `location.state.justPlaced` is set and payment is not `FAILED`. Shows the payment reference when present, and `failure_reason` when the order is not paid. The table is product, quantity, price, subtotal. Quantity is text.

Failed and not COD: Pay again → `POST /api/payments/process` → `retry_payment` (re-hold stock only when status is `FAILED`, then charge). The page replaces its order with the response. Failed, including COD: Return to cart → `POST /api/orders/{id}/return-to-cart` → delete the order after merging lines into the cart → `refreshCart` → `/cart`.

### `src/pages/ProfilePage.jsx`

`GET /api/auth/me` and `GET /api/orders/me` together. Keeps `payment_status === "PAID"` only. Phone is shown as `+91-` plus 10 digits. Role is not rendered. Empty paid list: “No placed orders yet.” Each row reuses `OrderListItem` and passes the payment-method label.

### `src/pages/NotFoundPage.jsx`

“Page not found” and a link to `/products`. Used by the `*` route.

## What these files do not call

No file calls port 9000, `/api/admin/*`, `/api/notifications/send`, or `/api/auth/token`. Refresh is only inside `client.js`. Admin, audit, and the manual notify route stay on the API for Swagger and tests.
