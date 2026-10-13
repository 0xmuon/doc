# Frontend interview notes

The customer uses a React app served by Vite. The browser only talks to `/api`, and Vite forwards that to the API on port 8000. Login is stored in the browser. Cart and orders call the API with the access token. The payment gateway is never called from the browser.

## The four tools, in this project

**JavaScript** is the language. Every file under `frontend/src` is JavaScript. A `.jsx` file is JavaScript that also contains the HTML-like markup for one piece of the screen.

**React** is the library that draws the screen. A component is a function that returns that markup. When its data changes, React draws it again. There is no separate HTML file per page. `index.html` has one empty `<div id="root">`. `main.jsx` puts the whole app inside that div.

**Vite** is the development server. `npm run dev` starts it, usually at `http://127.0.0.1:5173`. When you save a file, the page updates. `vite.config.js` says: any browser request that starts with `/api` goes to `http://localhost:8000`. That is why the shop code never writes port 8000 or 9000. Port 9000 is the fake payment API, and only the Python API calls it.

**ESLint** is the checker. `npm run lint` reads the code and reports mistakes, such as an unused variable or a state update in the wrong place. It does not run the shop. **Vitest** is the test runner. `npm test` runs four checks in `validate.test.js` for name, email, and quantity. Those tests do not open a browser.

**Tailwind** is how the pages are styled. There is one stylesheet, `src/index.css`, and it only loads Tailwind and sets the page margin to 0. There is no `Header.css` or `Login.css`. The look of each piece is written on that element as a `className`. In `Header.jsx`, `className="text-lg font-semibold text-red-600"` is the red brand, and `className="rounded-full bg-red-600 px-3 py-1 text-white"` is the logout button. Tailwind turns those names into real CSS while Vite runs. That is why the styles look individual even though they are not separate CSS files.

## How one screen is built

A **component** is a function. `ProductCard` receives a product and returns the card. The inputs are called **props**. `PropTypes` under the function says which props are required. That is the stand-in for TypeScript in this project. The project stayed in JavaScript, so props are checked with PropTypes instead of converting the app to TypeScript.

**State** is data the screen remembers. `useState` creates it. Changing it redraws the component. The search box text is state. The logged-in user is state.

**An effect** is `useEffect`. It runs after the screen appears. Pages use it to load products, the cart, or an order from the API.

**Context** is shared state. `AuthProvider` holds who is logged in. `CartProvider` holds the cart. They wrap the whole app in `App.jsx`, so the header and the pages see the same user and the same cart.

**The router** is `react-router-dom`. The URL picks the page. `App.jsx` is the map.

| URL | Page | Login required |
| --- | --- | --- |
| `/` and `/home` | Home | No |
| `/register`, `/login` | Register, login | No |
| `/products`, `/products/5` | List, one product | No |
| `/cart`, `/checkout` | Cart, checkout | Yes |
| `/orders`, `/orders/11` | History, one order | Yes |
| `/profile` | Profile | Yes |
| anything else | “Page not found” | No |

`Layout` draws the header, then the current page, then the footer. The current page is the `<Outlet />`. `ProtectedRoute` waits until the saved session has been checked. If nobody is logged in, it sends the browser to `/login` and remembers the page they wanted, so login can send them back.

## Folder map

`src/pages` is one file per screen. `src/components` is the pieces those screens reuse: header, menu, footer, product card, search box, status pill, protected route. `src/context` is login and cart. `src/api` is the only place that calls the server: `client.js` plus `authApi`, `cartApi`, `orderApi`, and `productApi`. `src/utils` is rules and helpers: validation, money, quantity, status labels. `src/hooks` is `useForm` for register and login, and `useDebouncedValue` for search.

`auth-context.js` and `cart-context.js` only export the hooks. The providers stay in `AuthContext.jsx` and `CartContext.jsx`. ESLint wants a file that exports a component not to also export a helper. Same reason `statusLabels` lives in `utils/statusLabels.js` instead of beside the pill component.

## What happens on login

Register checks the form in the browser before it calls the API.

- Name is required, at least 6 characters, letters only, one space between words.
- Email must look like an email.
- Password needs 8 characters, one uppercase, one lowercase, one number, one special character.
- Mobile must be 10 digits. That field is extra because this API rejects a registration without it.

The Register button stays disabled until every field is valid, and it stays disabled while the request runs. Reset clears the form. Errors show after the user leaves a field, and all of them if they submit. A duplicate email is shown under the email field.

Login only checks that the email looks valid and the password is not empty. Seed users such as `het@example.com` / `het12345` can log in even though that password would fail the register rule. The button is disabled until both fields are valid.

`POST /api/auth/login` returns an access token, a refresh token, and the user. Those go into `localStorage` under `abcshop_session`, plus the two token keys. Later calls send `Authorization: Bearer` and the access token. The refresh token is not sent on those calls. If a call returns 401, `client.js` posts the refresh token to `/api/auth/refresh` once, saves the new pair, and retries the original call. If that fails, the user is logged out. Logout only deletes the keys in this browser.

On refresh of the page, the app reads the saved session and calls `GET /api/auth/me`. Until that finishes, protected pages say “Checking your session...”.

The access token lasts 60 minutes. The refresh token lasts 7 days from the moment it is signed. A JWT does not renew itself. On a 401 the frontend posts the saved refresh token. The API then signs a new access token and a new refresh token, and the frontend stores that new refresh token. Coming back within 7 days of the last renewal keeps the session going. Staying away longer than that logs the user out on the next visit.

## Products, cart, checkout

The product list loads categories and products. The search box waits 300 milliseconds after the last keystroke, then searches. A typed word matches the product name through the API, and also a category name in the browser, because the API’s name search does not look at categories. The category dropdown is an exact category. If the user types again before the first answer arrives, the older answer is ignored. Out-of-stock products are sorted to the end. A card shows name, category, description, price as `INR 799`, stock, and “In cart: N”. If stock is 0, the button is replaced by “Out of Stock”.

Add to Cart adds one. It is disabled when the cart already holds all the stock or already holds 10. The cap of 10 comes from `VITE_MAX_QUANTITY_PER_ITEM`, default 10, and it sits on top of the stock check. A guest who clicks Add to Cart is sent to login with the message “Please log in to add items to your cart.”, then returned to that product. After a successful add, the page stays put.

The product page has a quantity box for how many to add on this click. An invalid number is shown and is not sent. The check includes what is already in the cart, so 8 in the cart plus 3 typed is over the cap of 10.

The cart page’s quantity box is the absolute quantity. It waits 500 milliseconds, then `PUT /api/cart/update/{id}`. A bad number shows an error and is not saved. Remove deletes the line. The item count and the total are added in the browser from the lines. The API cart has no total field. Checkout is disabled when the cart is empty or any line is over stock or over 10.

Checkout offers only Credit Card and Cash on Delivery. Place order posts `{ user_id, payment_method }`. The browser then always opens `/orders/{id}`.

Credit Card is charged by the Python API, which talks to port 9000. Paid shows “Thank you! Your order has been placed.” and the pills **Confirmed** and **Paid**. Failed opens the same order without the thank-you line, with the pill **Payment Failed**. Stock for that failure is released by the API. The cart is already empty. **Pay again** charges that order again. **Return to cart** puts the lines back in the cart, deletes that failed order, and opens the cart so the customer can add more and check out again. The order number is not reused. The next order gets the next id. The audit log still stores the old id.

Cash on Delivery never calls the payment gateway. The order is **Confirmed** and the payment stays **Pending Payment**, because the money is collected on delivery. Thank you is shown. Pay again is not shown. Stock stays reserved.

Order history is `GET /api/orders/me`, so it is only this user’s orders. An empty list says exactly “No orders found.” Details show every product, quantity, and price. A 403 says “You can only view your own orders.” A 404 says “Order not found.”

Profile shows name, email, phone as `+91-` plus the 10 digits, and hides the role. “Placed orders” on the profile are only orders whose payment status is `PAID`. A cash-on-delivery order stays on the Orders page until it is paid.

Prices are the letters `INR`, not the rupee sign. Whole amounts have no decimals.

## Answers you can say out loud

**Why is the cart in context?** The header shows `Cart (N)` and the product cards show “In cart: N”. One `CartProvider` loads the cart after login and every page reads that same list.

**Why validate in the browser if the API also checks?** The button can stay disabled, and the user sees the message before a request is sent. The API is still the real check. A duplicate email, a stock miss, and a bad token come back from the server and are shown on the page. If the response has a request id, the message ends with `(ref: …)`.

**What is StrictMode?** In `npm run dev`, React mounts effects, cleans them up, and mounts them again. You may see two identical GETs. A production build does not. The full explanation is in the StrictMode section below.

**What does `npm run build` do?** Vite writes a static `frontend/dist` folder. That is the site you would host. The API still has to be running separately.

**What did you not put in the frontend?** No admin screens. The browser does not call port 9000. UPI and net banking are not in the dropdown. Customer-service lines in the footer are text, not links, so they do not open a missing page.

## React concepts this codebase uses

Every screen is a function component. There are no class components. A component is a function that returns JSX, which is HTML-like markup inside JavaScript. `export default function Header()` is the header. `main.jsx` calls `createRoot` on the empty `<div id="root">` in `index.html` and renders `<App />` inside `<StrictMode>`.

**Props** are the inputs. `ProductCard` receives `product`, `cartQuantity`, `onChange`, `busy`, and `message`. The parent owns the data and passes down a function so the card can report a click. That is “lifting state”: the product list holds the cart change, the card only displays it. `children` is the special prop for whatever you wrap. `ProtectedRoute` and the providers use it. `PropTypes` checks those inputs in development: `string`, `number`, `bool`, `func`, `node`, and `shape`. `.isRequired` means the parent must pass it. This project did not switch to TypeScript. PropTypes is the check.

**State** is `useState`. Changing it redraws that component. Examples: the search text, the payment method, `busy` while a request runs, the loaded order. `useState(readSession)` reads `localStorage` on the first render. `useState(() => !readSession()?.token)` passes a function so that check runs only on the first render. Updates that depend on the previous value use the function form, `setSession((current) => ...)`, so two updates in a row do not overwrite each other.

**Derived values** are calculated during render and are not stored in state. The cart count is the sum of quantities. `overStock` is true when any line is above stock or above 10. On the product list, `loaded` is `loadedKey === requestKey`. That avoids clearing the list with `setState` at the start of an effect, which ESLint warns about.

**Effects** are `useEffect`. They run after paint, usually to fetch. The dependency array is the second argument. `[]` means once. `[productId]` means again when the id changes. The cleanup function runs before the next effect and on unmount. Search and product details set `ignore = true` in that cleanup so a slow older response cannot replace a newer one. The cart quantity timer and the search debounce clear the timeout in cleanup. The cart quantity effect also skips the update while that input is focused, so a parent refresh does not wipe what the user is typing.

**Refs** are `useRef`. They hold a value that must survive a redraw but must not cause one. `pendingRef` stops a double click from sending two adds. `timerRef` holds the cart-save timeout. `inputRef` points at the quantity input so the effect can ask `document.activeElement`.

**`useMemo` and `useCallback`** keep the context value stable. `AuthProvider` and `CartProvider` wrap the object they pass down in `useMemo`. `refreshCart` is wrapped in `useCallback` so the effect that loads the cart does not restart on every render. Without that, a new function every render would look like a new dependency.

**Context** shares one value with the whole tree. `createContext(null)` makes the box. The provider puts the value in it. `useContext` reads it. The custom hooks `useAuth` and `useCart` are that read, so pages do not import `useContext` themselves. `useForm` and `useDebouncedValue` are the other custom hooks. A custom hook is just a function whose name starts with `use` and that calls other hooks. Hooks are only called at the top of a component or hook, never inside an `if`.

The tree in `App.jsx` is `AuthProvider`, then `CartProvider`, then `BrowserRouter`. Cart is inside auth because the cart effect needs the token and the user. The router is inside both so every page can call `useAuth` and `useCart`.

**Conditional rendering** uses `condition ? a : b` and `condition ? <p>...</p> : null`. The header swaps the profile and logout controls for Login and Register. A list uses `.map`. The `key` on a product card is `product.product_id`, and on an order line it is `order_detail_id`. The key must be stable and unique in that list. The index is not used as the key.

**Events** are `onClick`, `onChange`, `onSubmit`, and `onBlur`. Forms are controlled: `value={form.values.email}` and `onChange={form.handleChange}`. React holds the text. The input does not keep its own copy. `onBlur` marks the field touched so the error can appear. `preventDefault` on submit stops the browser from reloading the page.

**Fragments** are `<>...</>`. The header uses them to return the profile link and the logout button together without an extra `<div>`.

**Router concepts from `react-router-dom`:**

- `BrowserRouter` listens to the real URL.
- `Routes` and `Route` pick the page. A parent route renders `Layout`. Child routes render into its `<Outlet />`.
- `Link` changes the URL without a full reload. `NavLink` knows whether it is the current page. Its `className` can be a function that receives `isActive`. Home is marked active for both `/` and `/home` by checking `useLocation().pathname`.
- `useParams` reads `:productId` and `:orderId`.
- `useNavigate` sends the user to another path after login, checkout, or return to cart.
- `useLocation().state` carries data that is not in the URL: the page to return to after login, the “please log in” message, and `justPlaced` for the thank-you line.
- `Navigate` in `ProtectedRoute` redirects. `replace` means the login page does not stack on the back button in place of the protected page.

**What this React app does not use.** No Redux, no `useReducer`, no `React.lazy`, no `Suspense`, no `memo`, no `forwardRef`, no class components, no CSS modules. None of those are in `package.json`. The reasons for the ones an interviewer is likely to ask about:

**Redux.** Redux is a separate library with one store and named actions. It helps when many distant screens share a large, frequently changing state and you want a log of every change. This shop shares two things: the logged-in user and the cart. `AuthProvider` and `CartProvider` already pass those to the header and the pages. A store and action names would only wrap “save this user” and “save this cart.”

**`useReducer`.** This is a React hook, not Redux. It fits when one event must change several fields together by fixed rules. Here each update stands alone: set `busy`, set the error, or replace the list with the API response. The cart count and `overStock` are calculated from the cart while rendering, so a reducer would not be keeping a second copy of them in step. `useState` matches “save this response” and “save this field.”

**`React.lazy`.** It loads a page’s JavaScript only when the user opens that page, together with `Suspense` for a fallback. This app is small. Every page loads with the first bundle. There is no split-bundle loading screen to maintain.

**Class components.** They are the older React style, with `this.state` and lifecycle methods such as `componentDidMount`. This project is React 19 function components and hooks (`useState`, `useEffect`, `useContext`). New code in this app follows that style, so there is no class component to keep in parallel.

## Tailwind, and why the classes sit on the elements

Tailwind version 4 is wired by the `@tailwindcss/vite` plugin in `vite.config.js`. There is no `tailwind.config.js`. `src/index.css` is the only stylesheet:

```css
@import "tailwindcss";

body {
  margin: 0;
}
```

`main.jsx` imports that file once. A `className` is a list of utility names. Tailwind generates the real CSS for the names the source files use. Unused names are not shipped.

The names used here:

- Layout: `flex`, `grid`, `min-h-screen`, `flex-1`, `max-w-6xl`, `mx-auto`, `gap-4`, `px-4`, `py-8`. The shell is a column at least as tall as the screen. `flex-1` on `<main>` pushes the footer to the bottom when the page is short.
- Type and color: `text-sm`, `text-2xl`, `font-semibold`, `text-red-600`, `text-slate-700`, `bg-white`, `bg-blue-600`, `bg-yellow-400`, `bg-rose-50/40`. The `/40` is 40 percent opacity.
- Variants: `hover:bg-blue-700` applies on hover. `disabled:opacity-50` applies while the button is disabled. `sm:flex-row` and `lg:grid-cols-3` apply from those widths up. `hidden sm:inline` hides the user’s name on a narrow screen and shows it from the `sm` breakpoint up.
- The product grid is one column, two columns from `sm`, three from `lg`.

There are no arbitrary values like `w-[137px]`. Spacing, color, and type come from Tailwind’s scale.

The reason to give: the class sits next to the element it styles, so the header color and the logout button are visible in `Header.jsx`. A separate `Header.css` would be a second name for a style Tailwind already provides. One `index.css` loads the system. Each component chooses which utilities it needs.

## How this runs on your PC

This is a local development setup, not a hosted deploy. Four processes matter.

| Process | Where | Port on your PC | Role |
| --- | --- | --- | --- |
| Vite | `frontend`, `npm run dev` | 5173 | The shop pages |
| API | Docker service `api` | 8000, debugger 5678 | FastAPI |
| Postgres | Docker service `db` | 5433 | The database |
| Fake payments and email | Docker service `provider` | 9000 | Charge and notify stand-in |

Start the three containers from the repo root with `docker compose up -d`. The compose project name is `shopping-simple`. Postgres must pass its health check before the API starts. The API image is `python:3.12-slim` from the `Dockerfile`. Compose replaces the image’s normal command with uvicorn `--reload` and debugpy on 5678. Your `app/`, `provider/`, and `tests/` folders are mounted into the container, so saving a Python file restarts the API without a rebuild.

Inside the Docker network the API reaches Postgres at host `db`, port 5432. From your PC the same database is `localhost:5433`. The volume `postgres_data` keeps the data across `docker compose down`. `docker compose down -v` deletes it. Seed with `docker compose exec api python -m app.db.seed`.

The browser never calls 8000 or 9000 directly. A fetch to `/api/...` hits Vite on 5173, and `vite.config.js` proxies it to `http://localhost:8000`. Inside Docker the API calls `http://provider:9000`. From your PC that same fake API is `http://localhost:9000`. `PUT http://localhost:9000/mode/ok`, `fail`, or `slow` changes both charges and emails. Leave it on `ok` when you are done.

`npm run build` writes static files to `frontend/dist`. That folder is what you would put on a web server. It still needs the API running somewhere, and the proxy exists only in `npm run dev`. A built site needs `VITE_API_BASE_URL` pointed at the real API, or a server that forwards `/api`.

Swagger for the shop API is `http://localhost:8000/docs`. The fake API docs are `http://localhost:9000/docs`. Logs are `docker compose logs api` and `docker compose logs provider`.

## Things worth saying if they ask

- Login JSON is `{ email, password }` to `POST /api/auth/login`. It is not a form body and it is not a username. Register sends `name`, `email`, `password`, and `mobile`.
- Roles `CUSTOMER`, `ADMIN`, and `SUPPORT` can all shop. The screens do not block admin or support from the cart.
- The access token lasts 60 minutes. The refresh token lasts 7 days and is rotated when `/api/auth/refresh` succeeds. Both live in `localStorage`. Logout does not tell the server.
- Cash on Delivery skips the gateway. The order is confirmed and payment stays pending. A failed card order can be paid again or returned to the cart. Return to cart deletes that order row. The id is not reused. The audit table still has the id.
- The circuit breaker lives in the API, not in React. Three failed charges go half-open, the next failure turns it off, and it stays off until the fake API mode is `ok`. A decline does not count.
- Notices are sent by the API after checkout and after pay again. Return to cart sends none. A failed notice does not change the order. Look for `order_notification_sent` or `order_notification_failed` in the API logs.
- Profile “Placed orders” means `payment_status === "PAID"` only. Cash on Delivery stays on the Orders page until it is paid.
- `npm run lint` is ESLint. `npm test` is four Vitest checks for name, email, and quantity. There is no browser test suite.
- In dev, StrictMode runs effects twice, so the network tab can show two identical GETs. A production build does not. See the StrictMode section.

## StrictMode

`main.jsx` wraps `<App />` in `<StrictMode>`. That wrapper is a development check. It does not draw anything and it is not a security mode. React turns the extra checks off in the production build from `npm run build`.

In development, React runs each effect, runs its cleanup, then runs the effect again. That is why the network tab shows two GETs for products, the cart, orders, or `/api/auth/me` when you first open a page. The first run is thrown away on purpose so a missing cleanup shows up during development. If an effect starts a timer or a fetch and does not cancel it, the second run would leak or would apply a stale answer.

This shop handles that in three places:

- Product search and product details set `ignore = true` in the effect cleanup. A response that belongs to the discarded run does not call `setState`.
- The search debounce and the cart quantity box clear their `setTimeout` in the cleanup.
- `pendingRef` blocks a second click while the first add or remove is still in flight. StrictMode does not replay click handlers, only effects, so a double click is a separate problem from the double GET.

StrictMode also warns if a component does something with a side effect during render. It does not double the user’s checkout, and it does not call the payment API twice by itself. A production build runs each effect once.

## Workflows

Every browser call goes through `src/api/client.js` `api()`. Vite on port 5173 proxies `/api` to the FastAPI app on port 8000. The Python route then calls a service, and the service calls a repository that reads or writes Postgres. The browser never calls port 9000.

### Open the site

`index.html` has `<div id="root">`. `main.jsx` renders `App` in StrictMode. `App.jsx` wraps `AuthProvider`, then `CartProvider`, then the router. `Layout` draws `Header`, the page (`Outlet`), and `Footer`.

`AuthProvider` reads `localStorage` key `abcshop_session`. If there is no token, `ready` is already true and public pages render. If there is a token, `GET /api/auth/me` runs. Backend: `auth_router.auth_me` → `get_current_user` reads the access token and loads the `Users` row. A 401 makes `client.js` call `POST /api/auth/refresh` → `user_service.refresh_session`, which checks the refresh token and signs a new pair. If refresh fails, the session is cleared and protected pages send the user to `/login`.

After `ready` is true and a user exists, `CartContext` runs `fetchCart` → `GET /api/cart/{userId}` → `cart_router.view_cart` → `cart_service.get_cart`.

Edge: while `ready` is false, `ProtectedRoute` shows “Checking your session...”. A guest who opens `/cart` is sent to `/login` with `state.from` set to `/cart`.

### Register

`RegisterPage` → `useForm` → `validateName`, `validateEmail`, `validatePassword`, `validateMobile` in `utils/validate.js`. The button stays disabled until `isValid`. Errors stay hidden until blur or submit (`touchAll`).

Submit calls `AuthContext.register` → `authApi.registerUser` → `POST /api/users/register` → `user_router.register` → `user_service` creates the `Users` row. Success navigates to `/login` with “Registration successful. Please log in.”

Edges:

- Name under 6 characters, a digit, or a double space: “Name can contain letters only.” or the length message. Nothing is sent.
- Bad email, weak password, or mobile that is not 10 digits: the field error shows. Nothing is sent.
- Duplicate email: API returns 409. The page shows “This email is already registered” under the email field.
- Any other server error is shown above the form, including `(ref: …)` when the API sent a request id.
- Reset clears values, touched fields, and the server error.
- The button says “Creating account...” and stays disabled while `busy` is true.

### Login

`LoginPage` checks email format and that the password is non-empty. Seed passwords such as `het12345` fail the register rule and still log in, because login does not apply the register password rule.

Submit → `AuthContext.login` → `POST /api/auth/login` → `user_service.login_user` checks the email and the password hash, then returns the access token, the refresh token, and the user. Those are stored in `abcshop_session`, `abcshop.accessToken`, and `abcshop.refreshToken`.

`safeReturnPath` in `auth-context.js` sends the user back to `location.state.from` only when that path starts with a single `/`. Otherwise they go to `/products`. A 401 shows “Invalid email or password”.

Logout in `Header` calls `AuthContext.logout`, which deletes the three storage keys. It does not call the API.

### Search and the product list

`ProductsPage` on first paint calls `fetchCategories` → `GET /api/categories` → `product_service.list_categories_async`.

The search box is `SearchBar`. It only updates `name`. `useDebouncedValue` waits 300 ms. The effect then calls `loadProducts`:

- No text and no dropdown: `GET /api/products` → `product_service.list_products` → active products only.
- Dropdown set: `GET /api/products/search?name=&category=` → `product_repository.search`. Category match is exact. Name, if also typed, is `ILIKE` on `product_name`. Both filters apply together.
- Text only: one search by name, plus a full product list. The page keeps name hits and also products whose `category_name` contains the text, because the API name filter does not look at the category. Duplicates are dropped by `product_id`.

After the response, products with `available_quantity <= 0` sort to the end. `loadedKey` must match the request key before the list is treated as loaded. The cleanup sets `ignore`, so a slower older search cannot overwrite a newer one.

Edges:

- Empty result: “No products found.”
- Request error: the red message, with the request id when the API sent one.
- `maxLength` on the box is 100.
- Out of stock: the card shows “Out of Stock” and no Add to Cart button (`ProductCard`).
- Missing category, description, or image: “Uncategorised”, “No description available.”, “No image”.

### Add to cart from the list or the product page

`ProductCard` calls `ProductsPage.changeQuantity`. `ProductDetailsPage.addToCart` checks the typed quantity and the resulting in-cart total against stock and the cap of 10 (`validateQuantity`, `MAX_QUANTITY_PER_ITEM`). An invalid number is shown and is not sent. A guest is sent to `/login` with “Please log in to add items to your cart.” and `from` set to the current path. The check runs before the redirect, so a bad quantity does not bounce a guest to login.

A valid add calls `utils/cartQuantity.js` `setCartQuantity`:

- No line yet: `POST /api/cart/add` → `cart_service.add_item`. Same product again increases that line.
- Line exists: `PUT /api/cart/update/{id}` → `cart_service.update_item`.
- Quantity under 1: `DELETE /api/cart/remove/{id}` → `cart_service.remove_item`.
- Over stock or over 10: thrown in the browser. The API also rejects a quantity above stock.

Then `CartContext.refreshCart` reloads `GET /api/cart/{userId}`. The list and the header count update. The product page stays on the same URL and resets Qty to 1.

Edges: the button is disabled when the cart already holds all the stock or already holds 10. `pendingRef` ignores a second click. The list button says “Updating...”. The details button says “Adding...”.

### Cart page

`CartPage` reads `useCart()`. Each line’s `CartQuantityInput` waits 500 ms after a valid change, then `updateCartItem`. An empty box, zero, a decimal, a value above stock, or a value above 10 shows the error and does not save. Remove calls `removeCartItem`. Totals are `inr()` sums in the browser. The API cart has no total field.

Checkout is disabled when the cart is empty or `overStock` is true. The message is “Not available in this quantity.”

Edges: while the input is focused, a cart refresh does not overwrite what is being typed. Leaving the page clears the pending timer.

### Checkout

`CheckoutPage.placeOrder` → `orderApi.placeOrder` → `POST /api/orders/checkout` with `{ user_id, payment_method }` → `order_router.checkout` → `order_service.checkout`.

`_reserve` locks the product rows, checks stock, creates the `Orders` row (`PENDING_PAYMENT` / `PENDING`), copies lines into `OrderDetails`, subtracts stock, deletes the cart lines, and commits. The order number becomes `ORD-` plus the id.

- `COD`: `_confirm_cod` sets `CONFIRMED` and `PENDING`. No call to port 9000. Stock stays reserved. Audit action `payment`, detail `PENDING`.
- `CARD`: `payment_gateway.charge_order` posts to `http://provider:9000/payments/charge`. Paid becomes `CONFIRMED` / `PAID`. Failed becomes `PAYMENT_FAILED` / `FAILED`, stock is released, and `failure_reason` is saved.

The router then queues `send_order_notification` → `POST http://provider:9000/notify`. A failed notice does not change the order.

The browser always opens `/orders/{id}`. `justPlaced` is set when payment status is not `FAILED`, so thank you shows for a paid card and for cash on delivery.

Edges:

- Empty cart or over-stock: the button is disabled and checkout returns immediately.
- Provider mode `fail`: card order is saved as failed, cart is already empty, pill is Payment Failed, no thank-you line.
- Provider mode `slow`: the charge times out and the order is failed the same way.
- Cash on delivery while the provider is in `fail`: the order still confirms. Only the notice can fail.

### One order, pay again, return to cart

`OrderDetailsPage` → `GET /api/orders/details/{id}` → `order_service.get_order`. A 403 shows “You can only view your own orders.” A 404 shows “Order not found.” `statusLabels` turns the two status fields into pills.

Pay again, only when `payment_status` is `FAILED` and the method is not `COD`: `POST /api/payments/process` → `ops_router.process_payment` → `order_service.retry_payment`. A failed order re-reserves stock in `_rehold`, then `charge_order` runs again. Success replaces the page data and the button goes away. Failure shows the error and leaves the order. Another notice is queued.

Return to cart, for any failed payment: `POST /api/orders/{id}/return-to-cart` → `order_service.return_to_cart`. Lines are merged into `CartItems`, stock is checked, the order and its details are deleted, an audit row `return_to_cart` is written, then `refreshCart` and navigate to `/cart`. The id is not reused.

Edges:

- Pay again on a paid order is not shown. If the API is called anyway, `retry_payment` returns the paid order and does not charge again.
- Cash on Delivery does not show Pay again. If `/api/payments/process` is called for `COD`, the API confirms it as pending and does not charge.
- Return to cart on a paid or pending order is not shown. The API rejects it with “Only an order with a failed payment can go back to the cart”.
- If the merged quantity would pass current stock, the API rejects the return and the order stays.
- Both buttons disable while either request runs.

### Order history and profile

`OrdersPage` → `GET /api/orders/me` → `order_service.list_orders` for the token’s user only. Zero rows show “No orders found.” Each row is `OrderListItem` with `statusLabels`.

`ProfilePage` calls `/api/auth/me` and `/api/orders/me`, then keeps rows whose `payment_status` is `PAID`. Phone display is `+91-` plus 10 digits. Role is not shown. An empty paid list says “No placed orders yet.” A cash-on-delivery order stays off this list until it is paid.

### Unknown URL

`App.jsx` route `*` renders `NotFoundPage`: “Page not found” and a link to `/products`. Footer Help Center, Returns, Shipping, and Contact Us are plain text, so they do not hit this route. Email and phone are real `mailto:` and `tel:` links.

## Easy to skip when you are new

These are not extra features. They are questions about the code you already have.

**This is a single-page app.** `Link` and `navigate` change the URL and React swaps the page inside `<Outlet />`. The browser does not download `index.html` again. A normal `<a href="/cart">` would reload the whole app and still work, but it would throw away the in-memory cart until `CartContext` fetched it again. Internal links use `Link`. Email and phone in the footer use `<a>` because they leave the site.

**Props versus context.** A product card receives its product and `onChange` as props because only the list needs that card. Login and the cart use context because the header, the menu, and many pages all read them. Passing the user through every component in between would be prop drilling. Context skips that middle line. The provider still has to wrap the readers. `CartProvider` sits inside `AuthProvider` because the cart request needs the token.

**One-way data.** Parents pass data down. Children tell the parent about a click by calling the function they were given. The card does not change the cart by itself. `ProductsPage` calls `setCartQuantity`, then `refreshCart`, and the new quantity comes back down as a prop. The screen does not guess. That is also why there is no optimistic update: the “In cart” number changes after the API succeeds, not before.

**Controlled inputs.** The React state is the value. `value={form.values.email}` plus `onChange` means the input cannot drift away from state. `noValidate` on the register and login forms turns off the browser’s own popup so the messages from `validate.js` are the ones the user sees.

**Keys.** `key={product.product_id}` tells React which row is which when the list is sorted or filtered. The array index would point at a different product after out-of-stock items move to the end, and the wrong card could keep the old button state.

**Effect dependency arrays.** `[]` runs after the first paint. `[productId]` runs again when that id changes. Leave out a value the effect uses and the effect can keep an old id. The cleanup runs before the next run. That is the `ignore` flag on search and product details.

**Every page has three shapes.** Loading (“Loading products...”), empty (“No products found.”, “Your cart is empty.”, “No orders found.”), and error (red text, often with `(ref: …)`). Buttons that send a request are disabled while `busy` and change their label. If they ask you to trace a screen, name which of the three is showing.

**The proxy is how the browser reaches the API in dev.** The page is on port 5173 and the API is on port 8000. Those are different origins. The browser would block a direct call from the page to 8000 unless the API sent CORS headers. The page instead calls `/api` on 5173, and Vite forwards it. There is no CORS setup in the React code. The proxy disappears in `npm run build`. A built site needs the host to forward `/api`, or `VITE_API_BASE_URL` set to the API. Only variables that start with `VITE_` are visible in the browser. `VITE_MAX_QUANTITY_PER_ITEM` and `VITE_API_BASE_URL` are the ones this app reads. The JWT secret never goes in a `VITE_` variable.

**JavaScript you should be able to point at.** `async`/`await` and `.then` for requests. `try/catch` around them. Destructuring (`const { user } = useAuth()`). The spread in `setValues((current) => ({ ...current, [name]: value }))`. Template strings for URLs and for `INR`. Array `.map` to draw lists, `.filter` for paid orders and category search, `.reduce` for the cart total, `.find` for the cart line, `.some` for `overStock`, `.sort` to put out-of-stock last.

**Debounce.** The search box updates state on every key. The API waits until 300 ms pass with no new key. The cart quantity box waits 500 ms. Both use a timer that the cleanup clears. That is not a React feature. It is a timer around `setState`.

**Security points that are actually in this code.** The password is not saved in `localStorage`. The access token is. Any script on this origin can read it. Logout does not revoke the token on the server. `safeReturnPath` refuses a return path that does not start with a single `/`. The browser never sends the refresh token except to `/api/auth/refresh`. Stock and price are checked again on the server at checkout. The button rules are only a convenience.

**There is no error boundary.** If a component throws while rendering, React unmounts the tree. Fetches are caught with `try/catch` and shown as text. A bug in the render itself is not caught. That is a fair “what would you add” answer, along with component tests. Today `npm test` only checks `validate.js`.

**What you would say if they ask what you would improve.** Store the refresh token in an `httpOnly` cookie and revoke it on logout. Add an error boundary. Add a test that renders the cart and the search, not only the validator. Paginate the product list if the catalog grew. Do not claim those exist now.
