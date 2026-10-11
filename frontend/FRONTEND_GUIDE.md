# SwiftShop frontend guide

This file is the walkthrough for the React shop in `frontend/`. It is only the website. The shopping API on port 8000 is a separate process. Use this when explaining the screens, the code path behind a click, and the small behaviors an evaluator will notice.

The brand on screen is **SwiftShop**. The week 4 brief is the source of the screens: register, login, product list and search, product details, cart, checkout with Credit Card or Cash on Delivery, and order history. Extra behavior that was added on top of that brief is called out below so you can say why it is there.

## How to run it in front of someone

1. From the repo root, start the API: `docker compose up`. The shop calls `http://localhost:8000`. If that process is down, every screen that loads data shows a failed request.
2. From `frontend/`, run `npm install` once, then `npm run dev`.
3. Open the URL Vite prints. It is usually `http://127.0.0.1:5173`. The browser tab title is SwiftShop.

The browser never calls port 9000. That port is the fake payment and email service. The API on port 8000 calls it during checkout. If you are asked “does the React app talk to the payment service?”, the answer is no.

`npm run build` produces a static `frontend/dist` folder. `npm run lint` runs oxlint. There is no frontend test suite.

## What the project is made of

Vite created the React JavaScript template. Tailwind v4 is attached in `vite.config.js` with `@tailwindcss/vite`. There is no `tailwind.config.js`. Styles are utility classes in the components, plus one line in `src/index.css`: `@import "tailwindcss"`. `src/main.jsx` renders `<App />` inside `StrictMode`. `src/App.css` is leftover from the template and is not imported.

`index.html` has the page title SwiftShop and a viewport meta tag, so the layout can shrink on a phone. The header hides the person’s name below the `sm` breakpoint and keeps the profile icon.

```text
frontend/src/
  main.jsx                 starts React
  App.jsx                  route table
  index.css                Tailwind
  services/api.js          every HTTP call
  context/AuthContext.jsx  who is logged in
  utils/validate.js        register and login checks
  utils/cartQuantity.js    add, change, or remove one cart line
  components/Layout.jsx    header, menu, footer around every page
  components/ProductCard.jsx
  components/QuantityStepper.jsx
  pages/                   one file per screen
```

A click does not talk to the database. The page calls `api()` in `services/api.js`. That function `fetch`es `http://localhost:8000` plus the path, sends JSON when there is a body, and sends `Authorization: Bearer <token>` when the caller passes a token. If the response is not OK, it throws `Error` with FastAPI’s `detail` string, or the joined `msg` fields when `detail` is a list of validation errors. The page catches that and shows `error.message` in red. The base URL is a constant. There is no frontend `.env`.

## The shell around every page

`App.jsx` wraps the site in this order: `AuthProvider`, then `BrowserRouter`, then `Layout`, then `Routes`. `Layout` always draws the header and footer. The matched page is the `<main>` in the middle.

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

There is no `*` route. A made-up path shows the header and footer with an empty main area.

The header brand **SwiftShop** and the **Home** links go to `/home`. The menu is Home, Products, Cart, Orders. The active link is blue and underlined. Home is also marked active on `/` because both paths are the home page. Products stays active on a product details URL, and Orders stays active on an order details URL, because those `NavLink`s are not limited to the exact path.

Logged out, the right side is a profile icon (goes to login), a blue **Login** button, and a white **Register** button. Logged in, the icon and the person’s name go to `/profile`, and **Log out** is red. Log out does not call the API. It deletes `localStorage` key `swiftshop_session` and clears React state. A page that requires login notices the token is gone and sends the browser to `/login`. Home and the product list stay where they are, because guests may view them.

The footer has four columns: a short shop blurb, Shop links, Customer Service labels, and contact. Home in the footer goes to `/home`. **Category**, **Deals**, and **New Arrivals** all go to `/products`. They are not separate catalogs. Help Center, Returns, Shipping, and Contact Us are plain text, not pages. Email is `support@swiftshop.com`. Phone is `+1 234 567 890` (`tel:+1234567890`), the number in the week 4 picture. Under the columns is `© 2026 SwiftShop. All Rights Reserved.`

Colors, on purpose: light rose page background, red for the brand and for cancel, logout, reset, and remove, blue for login and the main actions, yellow for Add to Cart, white for Register.

## Login state

`AuthContext.jsx` is the only place that stores the session.

- Storage key: `swiftshop_session`.
- Shape: `{ token, user }`. `token` is the access token from login. `user` is the API user: `user_id`, `name`, `email`, `mobile`, `role`, `is_active`.
- The refresh token from the login response is ignored. It is not saved.
- On first load, if a token exists, the app calls `GET /api/auth/me` and replaces `user` with that response. If `me` fails, the saved session is deleted. That is how an expired or bad token is dropped.
- `ready` stays false until that check finishes. Cart, checkout, orders, order details, and profile wait for `ready` before they decide to redirect. Without that wait, a refresh would flash the login page and then jump back.

Register calls `POST /api/users/register` and then navigates to `/login`. It does not log the new person in.

Login calls `POST /api/auth/login` with `{ email, password }` and then navigates to `/products`, not home.

There is no “return to the page you came from.” If a guest hits Add to Cart, they go to `/login`, and a successful login always lands on `/products`.

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
| Email | Required, must look like an email. Uniqueness is **not** checked here. The API rejects a duplicate and that text is shown in red. |
| Mobile | Exactly 10 digits. The week 4 form lists name, email, and password. This API refuses registration without a mobile number, so the field is here so an account can be created and an order can be placed. |
| Password | At least 8 characters, one uppercase, one lowercase, one digit, one special character. |

An error line appears only after that box is non-empty. An untouched empty form shows no red text, and **Register** stays disabled until every check passes. While the request is in flight the button says “Registering...” and stays disabled. **Reset** is red and clears the fields and the server error. It does not call the API.

The body sent is `{ name, email, password, mobile }` after trim on name, email, and mobile. Role is not sent. The API creates a CUSTOMER.

Demo seed passwords such as `het12345` do **not** satisfy the register rule. They have no uppercase letter and no special character. They still log in, because login does not apply that rule. If an evaluator tries to register with a seed password, the button stays disabled. That is expected.

### Login (`LoginPage.jsx`)

Fields: Email address, Password. Email uses the same format check. Password is required and nothing else, so the seeded accounts can sign in. **Login** is blue and disabled until both are valid, and it says “Logging in...” while busy. **Reset** clears the form. A wrong password or inactive account shows the API’s error text. Success goes to `/products`.

Seeded accounts, if the database was seeded:

| Name | Email | Password | Role on the API |
| --- | --- | --- | --- |
| Rudraksh | rudraksh@example.com | rudraksh1234 | ADMIN |
| Navya | navya@example.com | navya1234 | SUPPORT |
| Het | het@example.com | het12345 | CUSTOMER |

The website does not show the role and has no admin screens. All three people use the same shop. Each person only sees their own cart and their own orders, because those calls are tied to the token.

### Product list (`ProductsPage.jsx`, `ProductCard.jsx`)

On load: `GET /api/categories` fills the dropdown, and `GET /api/products` fills the grid. The dropdown value is the category **name**, plus “All categories”. Any category row in the database appears here, including one that was created during earlier API testing. The four seeded names are Electronics, Clothing, Books, and Home and Kitchen.

Search is live. Typing in “Search by name” or changing the category runs the effect again. There is no Search button and no debounce, so the network tab shows a request as the name changes. With both filters empty the call is `GET /api/products`. With either filter set it is `GET /api/products/search?name=&category=`. “No products found.” appears only after a successful response that returned an empty list. A failed request shows the error and does not also show “No products found.”

Each card shows the image, name, category, description, price as `INR` with no paise when the amount is a whole number, **In cart: N**, and a yellow **Add to Cart**. The **− N +** control is on that card only when this product’s cart count is already at least 1. A product that is not in the cart has Add to Cart and no stepper. After the first add, the count becomes 1 and the stepper appears. **−** down to zero removes the line and the stepper disappears again. The image and the name are the link to `/products/{id}`. The buttons are outside that link, so changing quantity does not open the details page. If `product_url` is empty, the card shows a gray “No image” box. If the URL is set but the picture host fails, the browser’s broken-image icon is what you see. There is no second fallback. The pictures in the seed are Unsplash URLs stored in `product_url`. The React code does not pick the photos itself. It renders whatever URL the API returns.

Out of stock (`available_quantity` is 0) hides the stepper and Add to Cart and shows “Out of Stock”. Those cards are moved to the end of the grid. In-stock cards keep the order the API returned. Search results use the same rule.

**In cart** comes from `GET /api/cart/{user_id}` when someone is logged in. Guests see 0. The page matches a cart line to a product by `product_id`. The API allows only one cart line per user and product, so that match is unique.

**+**, **−**, and **Add to Cart** all call `changeQuantity` in `ProductsPage.jsx`, which calls `setCartQuantity` in `utils/cartQuantity.js`:

- Not logged in: go to `/login`. Nothing is added.
- Next count above stock: show “Quantity cannot exceed available stock.” on that card. **+** and Add to Cart are also disabled when the count is already at stock.
- Next count below 1: `DELETE /api/cart/remove/{cart_item_id}`. **−** on a count of 1 removes the line. **−** is disabled at 0.
- No line yet: `POST /api/cart/add` with `{ user_id, product_id, quantity }`.
- Line already there: `PUT /api/cart/update/{cart_item_id}` with `{ quantity }` set to the new absolute count, not “add one” on top. Add to Cart means “make it current + 1”, same as **+**.

After a successful change the page reloads the cart and stays on `/products`. It does not open the cart. A second click while the first request is running is ignored (`pendingRef`). The button text becomes “Updating...”.

### Product details (`ProductDetailsPage.jsx`)

`GET /api/products/{productId}` loads one product. The same cart fetch finds this product’s line. The page shows description, price, available stock, **In cart**, the same stepper, and Add to Cart. “Back to products” goes to `/products`. The quantity rules are the same as the list, and the page stays on `/products/{id}`.

### Cart (`CartPage.jsx`)

Requires login. `GET /api/cart/{user_id}`.

Each line shows name, unit price, subtotal, **− quantity +**, and a red **Remove**. There is no typed quantity box and no separate Update button. **−** and **+** call the same update or delete routes. **Remove** sets the next quantity to 0, which deletes the line. **−** at 1 also deletes the line. **+** stops at `available_quantity`.

**Items** is the sum of quantities. **Total** is the sum of `line_total`. Both are computed in the browser. The API has no cart-summary route. Checkout is blue and disabled when the cart is empty. “Continue shopping” goes to `/products`.

### Checkout (`CheckoutPage.jsx`)

Requires login. Loads the same cart. The only payment choices are **Credit Card** (`CARD`) and **Cash on Delivery** (`COD`). UPI and net banking are not in the dropdown. Week 4 asks for card or cash.

**Place order** posts `POST /api/orders/checkout` with `{ user_id, payment_method }`. The button says “Placing order...” and is disabled while busy, and also when the cart is empty.

What happens next depends on `order.payment_status` in the response:

- `PAID`: the browser goes to `/orders/{order_id}`. That page is this order only, not the full history. The success text is not left on the checkout form.
- Anything else: the person stays on checkout. The message is “Payment was not completed. {order number} is on hold in your orders.” The cart list on this screen is cleared. The API has already turned the cart into an order and removed those cart lines, including when payment did not succeed. Stock for a failed payment is released by the API. The order remains and can be paid from its details page.

“View order history” still links to `/orders` if they want the full list instead.

### Order history (`OrdersPage.jsx`)

Requires login. `GET /api/orders/me`. These are only the logged-in user’s orders. An empty list shows the exact text “No orders found.”

Each row shows order number, local date and time (`toLocaleString`, so it follows the laptop’s locale), total, and a status word. `PAID` is blue **Placed**. Any other payment status is red **On hold**. **View details** goes to `/orders/{order_id}`.

### One order (`OrderDetailsPage.jsx`)

Requires login. `GET /api/orders/details/{orderId}`.

Heading is the order number, then Placed or On hold, the date, and a table of Product, Qty, Price, Subtotal. Qty here is text. A placed order’s quantities cannot be edited. Total is under the table. “Back to order history” goes to `/orders`.

If the order is not `PAID`, a blue **Pay again** button calls `POST /api/payments/process` with `{ order_id }`. On success the same page replaces its data, so a paid retry flips the label to Placed and the button goes away. On failure the order stays on screen and the error is shown under it. The button says “Trying payment...” while busy.

This is the page checkout opens after a successful place.

### Profile (`ProfilePage.jsx`)

Requires login. The header name and icon are the way in. `GET /api/auth/me` supplies name, email, and phone. A 10-digit mobile is shown as `+91-` plus those digits. The `+91` is display only. The API stores 10 digits. Role is not shown.

**Placed orders** is `GET /api/orders/me` filtered in the browser to `payment_status === "PAID"`. On-hold orders are not in this list. They remain on the Orders page. Each placed row shows number, date, “Credit Card” or “Cash on Delivery” (the API values `CARD` and `COD`), total, the word Placed, and View details. None yet says “No placed orders yet.”

## One shopping path, in order

Use this as the live demo.

1. Open the site. You are on Home, not the product grid.
2. Open Products. Search by a few letters and by a category. Open one product from its name.
3. As a guest, click **+**. You are sent to login. Sign in as Het. You land on the product list, not back on the product you touched.
4. On a product, use **+** and **−**. The **In cart** number changes and the URL stays on the product page.
5. Open Cart from the menu when you are ready. Change a quantity there too. The total changes without a reload.
6. Checkout, leave Credit Card selected, place the order.
7. You land on that order’s page, for example `/orders/6` with heading `ORD-000006`, and only that order’s lines.
8. Orders in the menu is the full history. Profile is the person’s phone and only the placed orders.

To show an on-hold order you need the fake payment API in fail mode. That is a backend switch, not a button in this website. After a failed checkout the message stays on the checkout page, the cart is empty, and the order appears under Orders as On hold, with Pay again on its details page.

## What the week 4 brief maps to

| Brief | Where it is |
| --- | --- |
| Header with brand, navigation, profile | `Layout.jsx` header |
| Menu of sections | Home, Products, Cart, Orders |
| Main content changes with the route | `App.jsx` routes inside `Layout` |
| Footer with shop links, contact, and copyright | `Layout.jsx` footer. Phone is `+1 234 567 890`. The line is `© 2026 SwiftShop. All Rights Reserved.` |
| Register name, email, password, validations, disabled until valid, reset | `RegisterPage.jsx`. Mobile is extra because the API requires it. |
| Login email and password, disabled until valid, reset | `LoginPage.jsx` |
| Product grid, search by name or category, Add to Cart, out of stock | `ProductsPage.jsx` |
| Product details | `ProductDetailsPage.jsx` |
| Cart quantity, remove, total, item count, checkout only if not empty | `CartPage.jsx`. Quantity is **−** and **+**, not a typed box. |
| Checkout, Credit Card or Cash on Delivery | `CheckoutPage.jsx` |
| Order history, details, “No orders found.” | `OrdersPage.jsx`, `OrderDetailsPage.jsx` |
| Buttons disabled while the request runs, server error shown | Each form and action button |

These were added because you asked for them. They are not in the week 4 PDF. Mobile on the register form is separate: the PDF lists name, email, and password, and the field is there only because this API rejects a registration with no mobile.

| What you asked for | What the site does |
| --- | --- |
| Light shopping colors: red for cancel, blue for login, yellow for Add to Cart, white for Register | Brand, logout, reset, and Remove are red. Login and the main actions (checkout, view details, pay again) are blue. Add to Cart is yellow. Register is white with a border. The page background is a light rose. |
| A real Home page, opened by default, reachable from the navbar | `/` and `/home` render `HomePage.jsx`. The site does not send you to `/products` on open. The header brand and both Home links go to `/home`. The page is four cards: Products, Cart, Orders, and Account. |
| Profile with the customer’s phone and the orders they have placed | `/profile` shows name, email, and phone. A 10-digit mobile is displayed as `+91-` plus the digits. Role is not shown. The order list is only rows whose payment status is `PAID`. On-hold orders stay on the Orders page. |
| Quantity as **−** and **+**, not a typed Qty box | Cart, the product list, and product details use `QuantityStepper.jsx`. There is no quantity text field and no separate Update button. |
| Stay on the product after Add to Cart | Adding or changing quantity on the list stays on `/products`. On the details page it stays on `/products/{id}`. The cart opens only when you choose Cart or Checkout. |
| On the product list, show **−** / **+** only after that product is already in the cart | The stepper is rendered when that product’s cart count is at least 1. At 0 the card has Add to Cart only. Taking it back to 0 hides the stepper. The details page still shows the stepper whenever the product is in stock, including at 0. |
| After a successful place, open that order | If `payment_status` is `PAID`, checkout navigates to `/orders/{order_id}` for that order only. |
| An order counts as placed only when payment succeeds | `PAID` is labeled **Placed**. Any other payment status is **On hold**. A failed checkout stays on the checkout page with “Payment was not completed. {order number} is on hold in your orders.” The API message was changed the same way. **Pay again** on the order details page calls `POST /api/payments/process` so that on-hold order can be paid without a new checkout. |
| Free product photos, with no copyright problem | Seed products use Unsplash image URLs in `product_url` (`app/db/seed.py`). The React code only displays the URL the API returns. |
| Prices in INR, written as the letters INR, not the rupee sign | `utils/money.js` formats money as `INR 6599`. Whole amounts have no paise. |
| Shop-style whole prices such as 5999 or 499 | `app/db/seed.py` stores whole rupee amounts ending in 99, the nearest such price to the old dollar amount times 83. Re-seeding writes those prices onto products that already exist. Orders placed before that change keep the totals saved at checkout. |
| Out-of-stock products at the end | `ProductsPage.jsx` sorts the grid so `available_quantity` of 0 comes last. In-stock cards keep the API’s order. Search uses the same sort. |

## Routes the screens call

| Method | Path | Used by |
| --- | --- | --- |
| POST | `/api/users/register` | Register |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Startup session check, and profile |
| GET | `/api/categories` | Category dropdown |
| GET | `/api/products` | Product list when search is empty |
| GET | `/api/products/search` | Name or category search |
| GET | `/api/products/{product_id}` | Product details |
| POST | `/api/cart/add` | First time a product’s count goes above zero |
| GET | `/api/cart/{user_id}` | Cart page, and the in-cart counts |
| PUT | `/api/cart/update/{cart_item_id}` | **+** or **−** when the line already exists |
| DELETE | `/api/cart/remove/{cart_item_id}` | Remove, or **−** down to zero |
| POST | `/api/orders/checkout` | Place order |
| GET | `/api/orders/me` | Order history, and the profile’s placed list |
| GET | `/api/orders/details/{order_id}` | One order |
| POST | `/api/payments/process` | Pay again |

`frontend/API_NOT_COVERED.md` lists the port 8000 routes this website does not call: the other login URL, refresh, admin catalog, admin orders, audit log, role change, health, metrics, and manual notification send.

## Small things that get asked

**Where is the money calculated?** Line totals come from the API (`line_total`, and on an order `price` and `line_total`). The cart page adds those line totals and the quantities itself for the summary. Checkout does the same addition for the total it displays. The server calculates the order total during checkout. The browser does not send a total.

**Can two fast clicks double the quantity?** A ref blocks a second cart change for that product until the first one finishes. The buttons are also disabled while it runs.

**Does Add to Cart and + differ?** No. Both set the next count to the current count plus one.

**Why does login land on products but the site opens on home?** Home is the default URL. After login the code calls `navigate("/products")` so the person can shop immediately.

**Why can I browse products with no account?** The list and the details page do not check the token. Cart, checkout, orders, order details, and profile do.

**Is the token a cookie?** No. It sits in `localStorage`. Any script on this origin can read it. Logout does not tell the server, so the token remains valid until it expires. The website never calls the refresh route.

**Why do I sometimes see two identical GETs in the network tab during `npm run dev`?** `main.jsx` uses `StrictMode`. In development React runs effects twice. A production build does not do that.

**Search feels chatty.** Each change of the name box or the category starts a new request. There is no delay.

**Dates and money.** Dates use the browser locale. Money is formatted as `INR` from `utils/money.js`. Whole amounts have no decimals (`INR 6599`). An amount that still has paise keeps two decimals. The letters INR are used, not the rupee sign. Seed prices are whole rupee shop prices ending in 99, the nearest such price to the earlier dollar amount times 83. Orders already placed keep the amounts saved at checkout.

**Images.** The card uses `product.product_url`. Empty string means the gray “No image” box. The Unsplash addresses are data, filled by `app/db/seed.py`, not by React.

**Footer “Deals” is not a sale.** It is the same product list as Category and New Arrivals.

**Profile “placed” is stricter than the Orders page.** Orders shows on-hold rows. Profile keeps only `PAID`.

**A failed payment still consumes the cart.** The order exists and is on hold. The items are not put back in the cart. Pay again is on that order’s page, not a new checkout of the same cart.

**Checkout only redirects when payment status is `PAID`.** That is the meaning of “order placed” on this site.

**Quantity on an old order is not the cart stepper.** The details table prints Qty. Changing it would change history, so the control is not there.

**No pagination, no wishlist, no address form, no admin UI, no frontend tests.** The only reorder is out-of-stock cards moving to the end. If the catalog grew, the list would still render every product the API returns.

**The API base URL is fixed** at `http://localhost:8000` in `services/api.js`. Opening the built files from another host still calls that URL.

**Guest cart count is always zero** until they log in. The count is not kept in `localStorage`.

**Register password rule and login password rule are different** on purpose, so the seeded passwords still work and new accounts still meet the week 4 rule.

**Name errors hide while the box is empty,** but the submit button stays disabled, so a blank form cannot be sent.

**Category, Deals, and New Arrivals do not filter.** Say that before someone clicks Deals and expects a different grid.
