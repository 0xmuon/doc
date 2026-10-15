# Frontend changes on 16-10-2026

What was added to the React shop on 16 October 2026. Behavior of login, cart, checkout, and orders is the same. The screens look more finished, registration confirms itself, and failed loads can be tried again.

## Look

Shared styles live in `frontend/src/index.css`. Pages use the same cards (`.panel`), fields (`.field`), and buttons:

- Blue for Login and the main actions
- White for Register
- Red for Log out, Reset, and Remove
- Yellow for Add to Cart

`frontend/index.html` loads the Source Sans 3 font.

| Area | What changed |
| --- | --- |
| Header | Sticky bar, red “A” mark, pill links for Home, Products, Cart, and Orders. On a narrow screen the links wrap onto their own row. |
| Footer | Dark bar. Phone `+1 234 567 890` and “© 2026 ABC Shop. All Rights Reserved.” are unchanged. |
| Home | Red banner, then the Products, Cart, Orders, and Account cards. |
| Login and Register | Centered card, clearer labels, focus ring on the fields. |
| Products | Taller image area, category line, stronger price. Out of stock stays at the end. |
| Product page | Image and details side by side on a wide screen. |
| Cart and checkout | Each line sits on a card. Total is called out. |
| Orders and profile | Same cards and status pills. Order lines sit in a table. |
| Missing page | Centered “Page not found” card. |

## Registration dialog

After a successful register, the form stays and a dialog opens.

- Title: “You are registered”
- Text says the account is ready and the shopper is being taken to login
- A countdown runs for 5 seconds
- **Go to login** skips the wait
- The login page shows “Registration successful. Please log in.” and the email is already filled in

File: `frontend/src/pages/RegisterPage.jsx`. Login reads that email from the route state in `frontend/src/pages/LoginPage.jsx`.

## Loading and errors

`frontend/src/components/common/StatusMessage.jsx` is used everywhere a page waits or fails.

- **Loading** is a spinner and a sentence, such as “Loading products...”
- **Error** is a red panel titled “Something went wrong”, the message from the API, and **Try again** where a second request can succeed
- A shorter red note is used for a failure that happens on a form that is already on screen (login, register, add to cart, pay again, return to cart)

| Screen | Loading | Error and retry |
| --- | --- | --- |
| Session gate | “Checking your session...” before a protected page decides | If a saved login is no longer valid, login shows “Your session ended. Please log in again.” |
| Products | “Loading products...” | Catalog failure gets **Try again**. A category-list failure is a note and does not hide products that already loaded. |
| Product | “Loading product...” | Missing product or a failed load gets **Try again** and **Back to products**. A failed add stays on the page as a note. |
| Cart | “Loading cart...” | A failed cart load is an error with **Try again**. It is no longer shown as an empty cart. A quantity or remove failure stays on the page as a note. |
| Checkout | “Loading checkout...” | Same cart-load error and **Try again**. A failed place-order stays on the form. |
| Orders | “Loading orders...” | **Try again** reloads the list. “No orders found.” is the empty list, not an error. |
| Order details | “Loading order...” | Not found, someone else’s order, or a failed load gets **Try again**. Pay again and Return to cart failures stay on the order as a note. |
| Profile | “Loading profile...” | **Try again** reloads the profile and the paid orders. |

`frontend/src/api/client.js` turns a dead connection into “The shop could not be reached. Check your connection and try again.” A 502, 503, or 504 becomes “The shop is unavailable right now. Try again in a moment.” Other API errors still include `(ref: …)` when the server sent a request id.

## Files touched

- `frontend/index.html`
- `frontend/src/index.css`
- `frontend/src/api/client.js`
- `frontend/src/components/common/ProtectedRoute.jsx`
- `frontend/src/components/common/StatusBadge.jsx`
- `frontend/src/components/common/StatusMessage.jsx` (new)
- `frontend/src/components/layout/Footer.jsx`
- `frontend/src/components/layout/Header.jsx`
- `frontend/src/components/layout/Layout.jsx`
- `frontend/src/components/layout/Menu.jsx`
- `frontend/src/components/orders/OrderListItem.jsx`
- `frontend/src/components/products/ProductCard.jsx`
- `frontend/src/components/products/SearchBar.jsx`
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/context/CartContext.jsx`
- `frontend/src/pages/CartPage.jsx`
- `frontend/src/pages/CheckoutPage.jsx`
- `frontend/src/pages/HomePage.jsx`
- `frontend/src/pages/LoginPage.jsx`
- `frontend/src/pages/NotFoundPage.jsx`
- `frontend/src/pages/OrderDetailsPage.jsx`
- `frontend/src/pages/OrdersPage.jsx`
- `frontend/src/pages/ProductDetailsPage.jsx`
- `frontend/src/pages/ProductsPage.jsx`
- `frontend/src/pages/ProfilePage.jsx`
- `frontend/src/pages/RegisterPage.jsx`
