# How this frontend differs from ecommerce2

`ecommerce2-fullstack.zip` is another React shop for the same week 4 brief. Its screens call a different API, so paths, field names, and a few rules cannot be copied across. This file is only the differences. Both shops still register, log in, list and search products, add to a cart, check out with Credit Card or Cash on Delivery, and show order history.

## The site opens on Home

Their `/` is the product grid. This shop opens `HomePage.jsx` at `/` and `/home`. The product grid is `/products`.

Why: you asked for a real Home page, reached from the header, instead of landing on the catalog.

```jsx
// ecommerce2/frontend/src/App.jsx
<Route index element={<ProductListPage />} />

// frontend/src/App.jsx
<Route path="/" element={<HomePage />} />
<Route path="/home" element={<HomePage />} />
<Route path="/products" element={<ProductsPage />} />
```

## Profile exists here

They have no profile route. The header icon goes to login or stays a customer marker. This shop has `/profile`: name, email, phone shown as `+91-` plus 10 digits, and only orders whose `payment_status` is `PAID`.

Why: you asked for the customer's phone and the orders they have placed. On-hold orders stay on the Orders page.

## Any logged-in role can use the shop

Their cart, checkout, and orders are wrapped so only `customer` can open them. An admin or support account is turned away. This shop's `ProtectedRoute` only checks that someone is logged in.

Why: this API allows an admin or support user to have a cart. Hiding those pages would not match the server.

```jsx
// ecommerce2
const CUSTOMER_ONLY = ["customer"];
<Route path="cart" element={customerPage(<CartPage />)} />

// this shop
<Route path="/cart" element={<ProtectedRoute><CartPage /></ProtectedRoute>} />
```

Their add-to-cart hook also throws if the person is not a customer. This shop does not.

```js
// ecommerce2/frontend/src/hooks/useAddToCart.js
if (!isCustomer) throw new Error("Only customer accounts can add items to a cart.");
```

## One `api()` function, not four API files

They split calls into `authApi.js`, `productApi.js`, `cartApi.js`, and `orderApi.js`. Each function forwards one path to `apiRequest`. This shop keeps every call in `src/api/client.js`. A page passes the path.

Why: this shop has about a dozen calls, and each path belongs to one screen. The extra files would only move the URL. Token refresh and error parsing already live in that one client. Their client is busier (login is a form body, search passes a query object), so the split fits them.

```js
// ecommerce2/frontend/src/api/cartApi.js
export function fetchCart() {
  return apiRequest("/api/cart");
}

// this shop, frontend/src/context/CartContext.jsx
const data = await api(`/api/cart/${user.user_id}`, { token });
```

## Login and register match this API

Their login posts a form field named `username`. Their register posts `full_name` to `/api/auth/register` and has no mobile field. This API expects JSON `{ email, password }` at `/api/auth/login`, and `{ name, email, password, mobile }` at `/api/users/register`.

Why: a copied call would be a 422. Mobile is on the form because this API rejects a registration that has no mobile. The week 4 form itself lists name, email, and password.

```js
// ecommerce2/frontend/src/api/authApi.js
form: { username: email.trim(), password }
body: { full_name: name.trim(), email: email.trim(), password }

// this shop, AuthContext.jsx
body: { email, password }                          // POST /api/auth/login
body: { name, email, password, mobile }            // POST /api/users/register
```

## The cart total is added in the browser

Their `GET /api/cart` already returns `total_items` and `total`. This cart response has lines only. `CartPage.jsx` and `CheckoutPage.jsx` add `quantity` for the count and `line_total` for the total.

Why: there is no cart-summary route on this API.

```js
// ecommerce2: GET /api/cart -> { items, total_items, total }

// this shop, CartPage.jsx
const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);
const total = cart.items.reduce((sum, item) => sum + Number(item.line_total), 0);
```

## Quantity is limited by stock, not by 10

Their validator refuses a quantity above stock and above `MAX_QUANTITY_PER_ITEM` (10 unless an env variable changes it). This shop's `validateQuantity` only checks a positive whole number against `available_quantity`.

Why: the week 4 brief limits quantity by stock. A cap of 10 is not in the brief.

```js
// ecommerce2/frontend/src/utils/validators.js
if (quantity > MAX_QUANTITY_PER_ITEM) return `At most ${MAX_QUANTITY_PER_ITEM} per product`;

// this shop, frontend/src/utils/validate.js
if (Number(text) > stock) return "Quantity cannot exceed available stock.";
```

## Add to Cart stays on the product and shows In cart

Their hook posts `POST /api/cart/add` with a quantity and the card says "Added to cart". This shop calls `setCartQuantity` in `utils/cartQuantity.js`. The first unit is `POST /api/cart/add`. A later click is `PUT /api/cart/update/{cart_item_id}` with the new absolute count. The card and the details page show **In cart: N**. The URL stays on `/products` or `/products/{id}`.

Why: you asked to stay on the product, and this API keeps one cart line per user and product, so the next click must update that line.

## Prices are the letters INR, and cards show the photo URL

Their `formatPrice` uses `Intl` currency style, which prints the rupee sign. Their API has no image, so the card shows initials from the name. This shop's `inr` prints `INR 6599` with no paise on a whole amount. The card uses `product.product_url`. An empty URL is a gray "No image" box. Seed rows store Unsplash URLs.

Why: you asked for the letters INR, not the rupee sign, and for product photos.

```js
// ecommerce2/frontend/src/utils/format.js
const priceFormatter = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" });

// this shop, frontend/src/utils/money.js
return `INR ${text}`;
```

## Placed means the payment succeeded

Their badge prints the API status as-is: Confirmed, Paid, Pending Payment, Payment Failed. After checkout they always open `/orders/{order.id}`, including when the card charge failed. This shop treats `payment_status === "PAID"` as blue **Placed** and anything else as red **On hold**. Checkout opens `/orders/{order_id}` only when the status is `PAID`. Otherwise the person stays on checkout and the message says the order is on hold. **Pay again** is only when the status is `FAILED`.

Why: you asked for "order placed" to mean the payment succeeded.

```jsx
// ecommerce2: always leave checkout
navigate(`/orders/${order.id}`, { state: { justPlaced: true } });

// this shop, CheckoutPage.jsx
if (data.order.payment_status === "PAID") {
  navigate(`/orders/${data.order.order_id}`);
}
```

Payment values differ for the same reason. They send the words `"Credit Card"` and `"Cash on Delivery"`. This API expects `CARD` and `COD`.

## Order and product fields use this API's names

| Their field or path | This shop |
| --- | --- |
| `product.id`, `product.name` | `product.product_id`, `product.product_name` |
| category filter by `category_id` | category filter by the category **name** |
| `GET /api/orders/{id}` | `GET /api/orders/details/{order_id}` |
| `order.id`, `order.created_at`, `order.status` | `order.order_id`, `order.order_date`, `order.payment_status` |

Why: those are the names this API returns. Renaming them in React would not match the JSON.

## Small components that were not copied

They have their own files for `Alert`, `FormField`, `Icon`, `Loader`, `CategoryFilter`, `CartItemRow`, `CartSummary`, `OrderItemsTable`, and `useAddToCart`. Those pieces sit inside the page that uses them here, because each one is a short block used once, or twice with a different rule.

Two shared files were added where the same rule was repeated: `StatusBadge.jsx` (Placed / On hold) and `OrderListItem.jsx` (the order card on Orders and Profile). Their `StatusBadge` is a pill that prints the raw status. Their `OrderListItem` also counts items from `order.items` and uses `order.id`. Profile passes a payment-method line into ours. Their history row does not.

## Footer links

Their Help Center, Returns, and Shipping are plain text, and the phone is `+91 98765 43210`. This footer sends Help Center, Returns, Shipping, and Contact Us to `/help-center`, `/returns`, `/shipping`, and `/contact`, which render **Page not found**. Category, Deals, and New Arrivals all go to `/products`. The phone is `+1 234 567 890`, and the copyright year is 2026.

Why: the week 4 picture uses that phone number, and you asked those four customer-service labels to open the not-found page. They are not catalogs.

## Out-of-stock cards move to the end

Both shops hide Add to Cart and show "Out of Stock" when stock is 0. This shop also sorts those cards to the end of the grid. Search uses the same sort. Their list keeps the API's order.

Why: you asked for out-of-stock products at the end.

## Neither frontend has a notification screen

Their React app never calls a notification route. A support or admin send lives on their API only. This React app never calls `POST /api/notifications/send` either. Checkout on this API already queues the email after the response. The screen does not send mail itself.
