# ABC Shop frontend guide

This file is the walkthrough for the React shop in `frontend/`. It is only the website. The shopping API on port 8000 is a separate process. Use this when explaining the screens, the code path behind a click, and the small behaviors an evaluator will notice.

The brand on screen is **ABC Shop**. The week 4 brief is the source of the screens: register, login, product list and search, product details, cart, checkout with Credit Card or Cash on Delivery, and order history. Extra behavior that was added on top of that brief is called out below so you can say why it is there.

## How to run it in front of someone

1. From the repo root, start the API: `docker compose up`. The shop calls `http://localhost:8000`. If that process is down, every screen that loads data shows a failed request.
2. From `frontend/`, run `npm install` once, then `npm run dev`.
3. Open the URL Vite prints. It is usually `http://127.0.0.1:5173`. The browser tab title is ABC Shop.

The browser never calls port 9000. That port is the fake payment and email service. The API on port 8000 calls it during checkout. If you are asked “does the React app talk to the payment service?”, the answer is no.

`npm run build` produces a static `frontend/dist` folder. `npm run lint` runs ESLint. `npm test` runs Vitest on `utils/validate.test.js` (name, email, and quantity rules). There is no browser test suite.

## What the project is made of

Vite created the React JavaScript template. Tailwind v4 is attached in `vite.config.js` with `@tailwindcss/vite`. There is no `tailwind.config.js`. Styles are utility classes in the components, plus one line in `src/index.css`: `@import "tailwindcss"`. `src/main.jsx` renders `<App />` inside `StrictMode`.

`index.html` has the page title ABC Shop and a viewport meta tag, so the layout can shrink on a phone. The header hides the person’s name below the `sm` breakpoint and keeps the profile icon.

```text
frontend/src/
  main.jsx                 starts React
  App.jsx                  route table
  index.css                Tailwind
  api/client.js            every HTTP call, including token refresh
  context/AuthContext.jsx  who is logged in
  context/CartContext.jsx  the cart and the header count
  hooks/useForm.js         field errors after blur and on submit
  hooks/useDebouncedValue.js
  utils/validate.js        register, login, and quantity checks
  utils/cartQuantity.js    add, change, or remove one cart line
  components/layout/       Header, Menu, Footer, Layout
  components/products/     ProductCard, SearchBar
  components/orders/       OrderListItem
  components/common/       ProtectedRoute, StatusBadge
  pages/                   one file per screen
```

A click does not talk to the database. The page calls `api()` in `api/client.js`. During `npm run dev`, Vite sends `/api` to `http://localhost:8000`, so the React code does not hard-code that host. The function sends JSON when there is a body, and sends `Authorization: Bearer <token>` when a token is available. If the response is not OK, it throws `ApiError` with FastAPI’s `detail` string, the HTTP status, and per-field messages when `detail` is a list. The page catches that and shows `error.message` in red.

## The shell around every page

`App.jsx` wraps the site in this order: `AuthProvider`, then `CartProvider`, then `BrowserRouter`, then a route whose element is `Layout`. `Layout` always draws the header and footer. The matched page is the `<Outlet>` in the middle. Cart, checkout, orders, order details, and profile are wrapped in `ProtectedRoute`, which sends a guest to `/login` and remembers that path.

| URL | Page file | Who can open it |
| --- | --- | --- |
| `/` and `/home` | `HomePage.jsx` | Anyone. Both URLs render the same page. |
| `/register` | `RegisterPage.jsx` | Anyone |
| `/login` | `LoginPage.jsx` | Anyone |
| `/products` | `ProductsPage.jsx` | Anyone |
| `/products/:productId` | `ProductDetailsPage.jsx` | Anyone |
| `/profile` | `ProfilePage.jsx` | Logged-in user. Otherwise sent to `/login`. |
| `/cart` | `CartPage.jsx` | Logged-in user. Otherwise sent to `/login`. |
| `/checkout` | `CheckoutPage.jsx` | Logged-in user. Otherwise sent to `/login`. |
| `/orders` | `OrdersPage.jsx` | Logged-in user. Otherwise sent to `/login`. |
| `/orders/:orderId` | `OrderDetailsPage.jsx` | Logged-in user. Otherwise sent to `/login`. |

A made-up path shows **Page not found** inside the header and footer.

The header brand **ABC Shop** and the **Home** links go to `/home`. The menu is Home, Products, Cart, Orders. **Cart** shows the item count in parentheses when it is above zero, from `CartContext`. The active link is blue and underlined. Home is also marked active on `/` because both paths are the home page. Products stays active on a product details URL, and Orders stays active on an order details URL, because those `NavLink`s are not limited to the exact path.

Logged out, the right side is a profile icon (goes to login), a blue **Login** button, and a white **Register** button. Logged in, the icon and the person’s name go to `/profile`, and **Log out** is red. Log out does not call the API. It deletes `localStorage` key `abcshop_session` and clears React state. A page that requires login notices the token is gone and sends the browser to `/login`. Home and the product list stay where they are, because guests may view them.

The footer has four columns: a short shop blurb, Shop links, Customer Service labels, and contact. Home in the footer goes to `/home`. **Category**, **Deals**, and **New Arrivals** all go to `/products`. They are not separate catalogs. Help Center, Returns, Shipping, and Contact Us go to `/help-center`, `/returns`, `/shipping`, and `/contact`. Those paths are not pages, so each one shows **Page not found**. Email is `support@abcshop.example`. Phone is `+1 234 567 890` (`tel:+1234567890`), the number in the week 4 picture. Under the columns is `© 2026 ABC Shop. All Rights Reserved.`

Colors, on purpose: light rose page background, red for the brand and for cancel, logout, reset, and remove, blue for login and the main actions, yellow for Add to Cart, white for Register.

## Login state

`AuthContext.jsx` is the only place that stores the session.

- Storage key: `abcshop_session`. The access token and the refresh token are also kept so a 401 can call `POST /api/auth/refresh` and retry the request once.
- Shape: `{ token, refreshToken, user }`. `token` is the access token. `refreshToken` is the refresh token. `user` is the API user: `user_id`, `name`, `email`, `mobile`, `role`, `is_active`. The same two tokens are also stored as `abcshop.accessToken` and `abcshop.refreshToken` so `api/client.js` can refresh without waiting for React.
- If a call returns 401, and it is not the refresh call itself, the client posts `{ refresh_token }` to `POST /api/auth/refresh`, saves the new pair, and retries the original request once. If refresh fails, the session is cleared.
- On first load, if a token exists, the app calls `GET /api/auth/me` and replaces `user` with that response. If `me` fails after a refresh attempt, the saved session is deleted.
- `ready` stays false until that check finishes. Cart, checkout, orders, order details, and profile wait for `ready` before they decide to redirect. Without that wait, a refresh would flash the login page and then jump back.

Register calls `POST /api/users/register` and then navigates to `/login` with the message “Registration successful. Please log in.” It does not log the new person in. A 409, or any error whose text mentions email, is shown under the Email field as “This email is already registered.” Other server errors stay as one red line above the buttons.

Login calls `POST /api/auth/login` with `{ email, password }` and then returns to the page that sent them to login. A direct login, with no page saved, goes to `/products`.

If a guest hits Add to Cart, they go to `/login` with “Please log in to add items to your cart.” A successful login returns to that product or the product list. The saved path must start with `/` and is never a full web address.

## Screen by screen

### Home (`HomePage.jsx`)

Opening the site shows Home. It does not redirect to the product list.

The page is four cards and no API call: Products, Cart, Orders, and Account. Each card links to that screen. Account repeats Login and Register. The copy matches the week 4 user tasks: browse and search, cart quantities and totals, checkout with card or cash, then order history.

### Register (`RegisterPage.jsx` and `utils/validate.js`)

Fields: Full Name, Email address, Mobile, Password. `noValidate` is set so the browser’s built-in bubbles do not fight the custom messages.

Checks, all in the browser before the request:

| Field | Rule |
| --- | --- |
| Name | Required, at least 6 characters, letters and spaces only. |
| Email | Required, must look like an email. Uniqueness is checked by the API on submit. A duplicate is shown under this field as “This email is already registered.” |
| Mobile | Exactly 10 digits. The week 4 form lists name, email, and password. This API refuses registration without a mobile number, so the field is here so an account can be created and an order can be placed. |
| Password | At least 8 characters, one uppercase, one lowercase, one digit, one special character. |

An error line appears after that box is left (`onBlur` in `useForm`), and every invalid field is shown if submit is attempted. An untouched empty form shows no red text, and **Register** stays disabled until every check passes. While the request is in flight the button says “Registering...” and stays disabled. **Reset** is red and clears the fields and the server error. It does not call the API.

The body sent is `{ name, email, password, mobile }` after trim on name, email, and mobile. Role is not sent. The API creates a CUSTOMER.

Demo seed passwords such as `het12345` do **not** satisfy the register rule. They have no uppercase letter and no special character. They still log in, because login does not apply that rule. If an evaluator tries to register with a seed password, the button stays disabled. That is expected.

### Login (`LoginPage.jsx`)

Fields: Email address, Password. Email uses the same format check. Password is required and nothing else, so the seeded accounts can sign in. Errors use the same blur-and-submit rule as register. **Login** is blue and disabled until both are valid, and it says “Logging in...” while busy. **Reset** clears the form. A 401 is shown as “Invalid email or password.” Any other failure shows the API’s error text. If login was opened from Add to Cart or from a protected page, success returns there. A login opened directly goes to `/products`.

Seeded accounts, if the database was seeded:

| Name | Email | Password | Role on the API |
| --- | --- | --- | --- |
| Rudraksh | rudraksh@example.com | rudraksh1234 | ADMIN |
| Navya | navya@example.com | navya1234 | SUPPORT |
| Het | het@example.com | het12345 | CUSTOMER |

The website does not show the role and has no admin screens. All three people use the same shop. Each person only sees their own cart and their own orders, because those calls are tied to the token.

### Product list (`ProductsPage.jsx`, `ProductCard.jsx`)

On load: `GET /api/categories` fills the dropdown, and `GET /api/products` fills the grid. The dropdown value is the category **name**, plus “All categories”. Any category row in the database appears here, including one that was created during earlier API testing. The four seeded names are Electronics, Clothing, Books, and Home and Kitchen.

Search is live. The name box waits 300 ms after typing stops, and a slow older answer is ignored if a newer search has already been sent. There is no Search button. With both filters empty the call is `GET /api/products`. With either filter set it is `GET /api/products/search?name=&category=`. “No products found.” appears only after a successful response that returned an empty list. A failed request shows the error and does not also show “No products found.”

Each card shows the image, name, category, description, price as `INR` with no paise when the amount is a whole number, **In cart: N**, and a yellow **Add to Cart**. Add to Cart adds one. The image and the name are the link to `/products/{id}`. The button is outside that link, so adding does not open the details page. If `product_url` is empty, the card shows a gray “No image” box. If the URL is set but the picture host fails, the browser’s broken-image icon is what you see. There is no second fallback. The pictures in the seed are Unsplash URLs stored in `product_url`. The React code does not pick the photos itself. It renders whatever URL the API returns.

Out of stock (`available_quantity` is 0) hides Add to Cart and shows “Out of Stock”. Those cards are moved to the end of the grid. In-stock cards keep the order the API returned. Search results use the same rule.

**In cart** comes from `GET /api/cart/{user_id}` when someone is logged in. Guests see 0. The page matches a cart line to a product by `product_id`. The API allows only one cart line per user and product, so that match is unique.

**Add to Cart** calls `changeQuantity` in `ProductsPage.jsx`, which calls `setCartQuantity` in `utils/cartQuantity.js` with the current count plus one:

- Not logged in: go to `/login` with “Please log in to add items to your cart.” Nothing is added. After login the browser comes back to this page.
- Already at stock: the button is disabled. If the next count would pass stock, the card shows “Quantity cannot exceed available stock.”
- No line yet: `POST /api/cart/add` with `{ user_id, product_id, quantity }`.
- Line already there: `PUT /api/cart/update/{cart_item_id}` with `{ quantity }` set to the new absolute count.

After a successful change the page reloads the cart and stays on `/products`. It does not open the cart. A second click while the first request is running is ignored (`pendingRef`). The button text becomes “Updating...”.

### Product details (`ProductDetailsPage.jsx`)

`GET /api/products/{productId}` loads one product. A 404 is shown as “Product not found.” The cart context finds this product’s line. The page shows description (or “No description available.”), category (or “Uncategorised”), price, **SKU**, “N in stock”, **In cart**, a Qty box, and Add to Cart. Qty starts at 1 and is how many to add this time. It must be a positive whole number and cannot pass the stock still left. An invalid Qty shows the error and Add to Cart does not call the API. A valid add stays on `/products/{id}`. “Back to products” goes to `/products`. `ProductCard` checks its props with PropTypes.

### Cart (`CartPage.jsx`)

Requires login. `GET /api/cart/{user_id}`.

Each line shows name, unit price, subtotal, a Qty box, and a red **Remove**. Qty must be a positive whole number and cannot pass `available_quantity`. An empty box, zero, a decimal, or a number above stock shows the error under that line and is not sent. A valid change waits briefly, then `PUT /api/cart/update/{cart_item_id}` with that absolute quantity. **Remove** deletes the line. It is the way to take the quantity to zero.

**Items** is the sum of quantities. **Total** is the sum of `line_total`. Both are computed in the browser. The cart response has no total field, so the browser adds the lines. Checkout is blue and disabled when the cart is empty, and also when any line’s quantity is above `available_quantity`. That case shows “Not available in this quantity.” “Continue shopping” goes to `/products`. The same count is what the header Cart link shows.

### Checkout (`CheckoutPage.jsx`)

Requires login. Loads the same cart. The only payment choices are **Credit Card** (`CARD`) and **Cash on Delivery** (`COD`). UPI and net banking are not in the dropdown. Week 4 asks for card or cash.

**Place order** posts `POST /api/orders/checkout` with `{ user_id, payment_method }`. The button says “Placing order...” and is disabled while busy, when the cart is empty, and when a line is above the stock left.

What happens next depends on `order.payment_status` in the response:

- `PAID`: the browser goes to `/orders/{order_id}`. That page is this order only, not the full history. The success text is not left on the checkout form.
- Anything else: the person stays on checkout. The message is “Payment was not completed. {order number} is on hold in your orders.” The cart list on this screen is cleared. The API has already turned the cart into an order and removed those cart lines, including when payment did not succeed. Stock for a failed payment is released by the API. The order remains and can be paid from its details page.

“View order history” still links to `/orders` if they want the full list instead.

### Order history (`OrdersPage.jsx`)

Requires login. `GET /api/orders/me`. These are only the logged-in user’s orders. An empty list shows the exact text “No orders found.”

Each row shows order number, local date and time (`toLocaleString`, so it follows the laptop’s locale), total, and a status word. `PAID` is blue **Placed**. Any other payment status is red **On hold**. **View details** goes to `/orders/{order_id}`.

### One order (`OrderDetailsPage.jsx`)

Requires login. `GET /api/orders/details/{orderId}`.

Heading is the order number, then Placed or On hold, the date, and a table of Product, Qty, Price, Subtotal. Qty here is text. A placed order’s quantities cannot be edited. Total is under the table. If the API sent `payment_reference`, it is shown. If the order is not paid and `failure_reason` is set, that sentence is shown. A 403 is “You can only view your own orders.” A 404 is “Order not found.” “Back to order history” goes to `/orders`.

If `payment_status` is `FAILED`, a blue **Pay again** button calls `POST /api/payments/process` with `{ order_id }`. A paid order and an order that is only pending do not show it. On success the same page replaces its data, so a paid retry flips the label to Placed and the button goes away. On failure the order stays on screen and the error is shown under it. The button says “Trying payment...” while busy.

This is the page checkout opens after a successful place.

### Profile (`ProfilePage.jsx`)

Requires login. The header name and icon are the way in. `GET /api/auth/me` supplies name, email, and phone. A 10-digit mobile is shown as `+91-` plus those digits. The `+91` is display only. The API stores 10 digits. Role is not shown.

**Placed orders** is `GET /api/orders/me` filtered in the browser to `payment_status === "PAID"`. On-hold orders are not in this list. They remain on the Orders page. Each placed row shows number, date, “Credit Card” or “Cash on Delivery” (the API values `CARD` and `COD`), total, the word Placed, and View details. None yet says “No placed orders yet.”

## One shopping path, in order

Use this as the live demo.

1. Open the site. You are on Home, not the product grid.
2. Open Products. Search by a few letters and by a category. Open one product from its name.
3. As a guest, open one product and click **Add to Cart**. You are sent to login, and the page says to log in to add items. Sign in as Het. You return to that product, not to a random page.
4. Open a product, leave Qty at 1, and click **Add to Cart**. **In cart** becomes 1 and the URL stays on that product. Type `0` or a number above the stock and the error shows. Nothing is added.
5. Open Cart from the menu when you are ready. Type a new Qty. An invalid number shows an error and the total stays. A valid number updates the total.
6. Checkout, leave Credit Card selected, place the order.
7. You land on that order’s page, for example `/orders/6` with heading `ORD-000006`, and only that order’s lines.
8. Orders in the menu is the full history. Profile is the person’s phone and only the placed orders.

To show an on-hold order you need the fake payment API in fail mode. That is a backend switch, not a button in this website. After a failed checkout the message stays on the checkout page, the cart is empty, and the order appears under Orders as On hold. Pay again is on its details page only when `payment_status` is `FAILED`.

## What the week 4 brief maps to

| Brief | Where it is |
| --- | --- |
| Header with brand, navigation, profile | `components/layout/Header.jsx` |
| Menu of sections | Home, Products, Cart, Orders |
| Main content changes with the route | `App.jsx` routes inside `Layout` |
| Footer with shop links, contact, and copyright | `components/layout/Footer.jsx`. Phone is `+1 234 567 890`. The line is `© 2026 ABC Shop. All Rights Reserved.` |
| Register name, email, password, validations, disabled until valid, reset | `RegisterPage.jsx`. Mobile is extra because the API requires it. |
| Login email and password, disabled until valid, reset | `LoginPage.jsx` |
| Product grid, search by name or category, Add to Cart, out of stock | `ProductsPage.jsx` |
| Product details | `ProductDetailsPage.jsx` |
| Cart quantity, remove, total, item count, checkout only if not empty | `CartPage.jsx`. Qty is a typed box. An invalid number shows an error and is not saved. |
| Checkout, Credit Card or Cash on Delivery | `CheckoutPage.jsx` |
| Order history, details, “No orders found.” | `OrdersPage.jsx`, `OrderDetailsPage.jsx` |
| Buttons disabled while the request runs, server error shown | Each form and action button |

These were added because you asked for them. They are not in the week 4 PDF. Mobile on the register form is separate: the PDF lists name, email, and password, and the field is there only because this API rejects a registration with no mobile.

| What you asked for | What the site does |
| --- | --- |
| Light shopping colors: red for cancel, blue for login, yellow for Add to Cart, white for Register | Brand, logout, reset, and Remove are red. Login and the main actions (checkout, view details, pay again) are blue. Add to Cart is yellow. Register is white with a border. The page background is a light rose. |
| A real Home page, opened by default, reachable from the navbar | `/` and `/home` render `HomePage.jsx`. The site does not send you to `/products` on open. The header brand and both Home links go to `/home`. The page is four cards: Products, Cart, Orders, and Account. |
| Profile with the customer’s phone and the orders they have placed | `/profile` shows name, email, and phone. A 10-digit mobile is displayed as `+91-` plus the digits. Role is not shown. The order list is only rows whose payment status is `PAID`. On-hold orders stay on the Orders page. |
| Stay on the product after Add to Cart | Adding on the list stays on `/products`. On the details page it stays on `/products/{id}`. The cart opens only when you choose Cart or Checkout. |
| After a successful place, open that order | If `payment_status` is `PAID`, checkout navigates to `/orders/{order_id}` for that order only. |
| An order counts as placed only when payment succeeds | `PAID` is labeled **Placed**. Any other payment status is **On hold**. A failed checkout stays on the checkout page with “Payment was not completed. {order number} is on hold in your orders.” The API message was changed the same way. **Pay again** is shown only when `payment_status` is `FAILED`, and it calls `POST /api/payments/process`. |
| Free product photos, with no copyright problem | Seed products use Unsplash image URLs in `product_url` (`app/db/seed.py`). The React code only displays the URL the API returns. |
| Prices in INR, written as the letters INR, not the rupee sign | `utils/money.js` formats money as `INR 6599`. Whole amounts have no paise. |
| Shop-style whole prices such as 5999 or 499 | `app/db/seed.py` stores whole rupee amounts ending in 99, the nearest such price to the old dollar amount times 83. Re-seeding writes those prices onto products that already exist. Orders placed before that change keep the totals saved at checkout. |
| Out-of-stock products at the end | `ProductsPage.jsx` sorts the grid so `available_quantity` of 0 comes last. In-stock cards keep the API’s order. Search uses the same sort. |

## What was taken from the other frontend, and what stayed

None of this changed the API. The React app only started calling routes that were already on port 8000, including `POST /api/auth/refresh`.

Taken from the other frontend, because the week 4 PDF asks for it or because it is the safer production behavior:

| Choice | Why |
| --- | --- |
| `Header`, `Menu`, and `Footer` are separate files | The PDF asks for those as React components. |
| **Page not found** | A bad URL should not be a blank main area. |
| Login returns to the page that sent you there, with “Please log in to add items to your cart.” | The saved path must start with `/`. A full web address is refused, so this cannot be used as an open redirect. |
| “Registration successful. Please log in.” | The person sees that the account was created. |
| Duplicate email under the Email field | The PDF says uniqueness is checked against existing users, and the error belongs on that field. |
| Errors after leaving a field, and all of them if submit is attempted | The PDF says to show errors on submission. The button still stays disabled until the form is valid. |
| Refresh token, one retry after 401 | The PDF asks for secure authentication. This API already issues a refresh token. |
| Search waits 300 ms, and an older answer cannot overwrite a newer one | The PDF says the search filters as the person types, and a late response must not show the wrong list. |
| Checkout blocked when a line is above the stock left | The PDF says quantity cannot exceed available stock. |
| Cart link shows the item count | One `CartContext` keeps the header and the pages on the same cart. |
| SKU, “N in stock”, “No description available.”, “Uncategorised” | The PDF says product cards must not leave required fields blank. |
| “Product not found.”, “Order not found.”, “You can only view your own orders.” | Clear 404 and 403 text. |
| PropTypes on the product card, Vitest on the validators | The PDF says to use strict typing and avoid `any`. This project stays JavaScript, so PropTypes and tests are how that is met. |
| Vite proxies `/api` to port 8000 | The React code does not hard-code the API host during `npm run dev`. |

Kept from this app, because it matches this API or a choice you already made:

| Kept | Why it was not replaced |
| --- | --- |
| Home, profile, photos, `INR` letters, out-of-stock cards last, **In cart: N** | These are extras you asked for. The other site does not have them. |
| Typed Qty, with an error, and no cap of 10 | The PDF limits quantity by stock. A max of 10 is not in the PDF. |
| **Placed** only when payment is `PAID`, otherwise **On hold**, and checkout stays put | You asked for that meaning of “order placed.” Pay again is only on an order whose `payment_status` is `FAILED`. `failure_reason` and `payment_reference` are shown when the API sends them. |
| Red, blue, yellow, and white buttons, phone `+1 234 567 890`, copyright year 2026 | Your color rules and the week 4 picture. The brand text is now ABC Shop. |
| Cart total added in the browser from `line_total` | This cart response has no total field. |
| Admin and support can use the same shop screens | This API allows their carts. Hiding those pages would not match the server. |

## Routes the screens call

| Method | Path | Used by |
| --- | --- | --- |
| POST | `/api/users/register` | Register |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Startup session check, and profile |
| POST | `/api/auth/refresh` | Once, after a 401, before the original request is retried |
| GET | `/api/categories` | Category dropdown |
| GET | `/api/products` | Product list when search is empty |
| GET | `/api/products/search` | Name or category search |
| GET | `/api/products/{product_id}` | Product details |
| POST | `/api/cart/add` | First time a product’s count goes above zero |
| GET | `/api/cart/{user_id}` | Cart page, and the in-cart counts |
| PUT | `/api/cart/update/{cart_item_id}` | A valid Qty on the cart, or Add to Cart when the line already exists |
| DELETE | `/api/cart/remove/{cart_item_id}` | Remove |
| POST | `/api/orders/checkout` | Place order |
| GET | `/api/orders/me` | Order history, and the profile’s placed list |
| GET | `/api/orders/details/{order_id}` | One order |
| POST | `/api/payments/process` | Pay again |

`frontend/API_NOT_COVERED.md` lists the port 8000 routes this website does not call: the other login URL, admin catalog, admin orders, audit log, role change, health, metrics, and manual notification send. Refresh is called, from `api/client.js`, not from a screen.

## Small things that get asked

**Where is the money calculated?** Line totals come from the API (`line_total`, and on an order `price` and `line_total`). The cart page adds those line totals and the quantities itself for the summary. Checkout does the same addition for the total it displays. The server calculates the order total during checkout. The browser does not send a total.

**Can two fast clicks double the quantity?** A ref blocks a second cart change for that product until the first one finishes. The buttons are also disabled while it runs.

**What counts as an invalid quantity?** Empty, zero, a fraction, or a number above the stock left. The cart does not save it. On the product page, Add to Cart does not run. **Remove** is the way to delete a cart line.

**Why does a direct login land on products while the site opens on home?** Home is the default URL. Login returns to the saved path. If there is no saved path, it goes to `/products`.

**Why can I browse products with no account?** The list and the details page do not check the token. Cart, checkout, orders, order details, and profile do.

**Is the token a cookie?** No. The access token and the refresh token sit in `localStorage`. Any script on this origin can read them. Logout does not tell the server, so the tokens remain valid until they expire. A 401 does call the refresh route once.

**Why do I sometimes see two identical GETs in the network tab during `npm run dev`?** `main.jsx` uses `StrictMode`. In development React runs effects twice. A production build does not do that.

**Search waits.** The name box waits 300 ms after the last keystroke. Changing the category starts a request immediately. An older response is ignored if a newer search is already in flight.

**Dates and money.** Dates use the browser locale. Money is formatted as `INR` from `utils/money.js`. Whole amounts have no decimals (`INR 6599`). An amount that still has paise keeps two decimals. The letters INR are used, not the rupee sign. Seed prices are whole rupee shop prices ending in 99, the nearest such price to the earlier dollar amount times 83. Orders already placed keep the amounts saved at checkout.

**Images.** The card uses `product.product_url`. Empty string means the gray “No image” box. The Unsplash addresses are data, filled by `app/db/seed.py`, not by React.

**Footer “Deals” is not a sale.** It is the same product list as Category and New Arrivals.

**Profile “placed” is stricter than the Orders page.** Orders shows on-hold rows. Profile keeps only `PAID`.

**A failed payment still consumes the cart.** The order exists and is on hold. The items are not put back in the cart. Pay again is on that order’s page when the payment status is `FAILED`, not a new checkout of the same cart.

**Checkout only redirects when payment status is `PAID`.** That is the meaning of “order placed” on this site.

**Quantity on an old order is text.** The details table prints Qty. Changing it would change history, so the box is not there.

**No pagination, no wishlist, no address form, no admin UI.** The only frontend tests are the validator checks in `npm test`. The only reorder is out-of-stock cards moving to the end. If the catalog grew, the list would still render every product the API returns.

**The dev server proxies `/api` to port 8000.** A production build uses `VITE_API_BASE_URL` when that variable is set, and otherwise calls `/api` on the same host.

**Guest cart count is always zero** until they log in. The count is not kept in `localStorage`.

**Register password rule and login password rule are different** on purpose, so the seeded passwords still work and new accounts still meet the week 4 rule.

**Name errors stay hidden until the box is left or submit is attempted,** and the submit button stays disabled, so a blank form cannot be sent.

**Category, Deals, and New Arrivals do not filter.** Say that before someone clicks Deals and expects a different grid.
