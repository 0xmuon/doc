# Added beyond the week 4 brief

`week4.pdf` asks for the user module: register and login, product list and search, product details, cart, checkout with Credit Card or Cash on Delivery, and order history. The pictures use the name SwiftShop, dollar prices, and no separate home or profile screen.

The rows below are in this shop and are not asked for in that brief. The brief does say extra features are allowed.

| What was added | What the site does |
| --- | --- |
| A Home page, opened first | `/` and `/home` show `HomePage.jsx`. The site does not open on the product grid. The header brand and both Home links go to `/home`. The page is four cards: Products, Cart, Orders, and Account. |
| A profile page | The header icon and name go to `/profile`. The page shows name, email, and phone. A 10-digit mobile is shown as `+91-` plus those digits. Role is not shown. The list is only orders whose payment status is `PAID`. |
| Mobile on the register form | The brief lists name, email, and password. This API rejects a registration with no mobile, so the form also asks for exactly 10 digits. |
| Button and page colors | The page background is a light rose. Brand, logout, reset, and Remove are red. Login and the main actions (checkout, view details, pay again) are blue. Add to Cart is yellow. Register is white with a border. |
| The name ABC Shop, and the copyright year 2026 | The pictures say SwiftShop and © 2024, and they include “Powered by React.” This site says ABC Shop, which matches the ABC organization in the brief. The footer line is `© 2026 ABC Shop. All Rights Reserved.` The support address is `support@abcshop.example`. The phone `+1 234 567 890` is the number in the picture. |
| Stay on the product after Add to Cart | Adding from the list stays on `/products`. Adding from the details page stays on `/products/{id}`. The cart opens only from Cart or Checkout. |
| **In cart: N** | The product card and the product page show how many of that product are already in the cart. A guest sees 0. |
| Cart count in the header | The Cart link shows the item count in parentheses when it is above zero. |
| A guest must log in before a cart change | Add to Cart sends a guest to `/login` with “Please log in to add items to your cart.” After login they return to that product or the product list. |
| After a successful place, open that order | If `payment_status` is `PAID`, checkout goes to `/orders/{order_id}` for that order only. |
| Placed only when payment succeeds | `PAID` is labeled **Placed**. Any other payment status is **On hold**. A failed checkout stays on the checkout page: “Payment was not completed. {order number} is on hold in your orders.” **Pay again** is shown only when `payment_status` is `FAILED`. `failure_reason` and `payment_reference` are shown when the API sends them. |
| Product photos | Seed products store Unsplash image URLs in `product_url` (`app/db/seed.py`). The React code displays that URL. An empty URL shows a gray “No image” box. |
| Prices written as `INR` | `utils/money.js` formats money as `INR 6599`. Whole amounts have no paise. The rupee sign is not used. The pictures use dollar amounts. |
| Shop prices ending in 99 | `app/db/seed.py` stores whole rupee amounts ending in 99, the nearest such price to the old dollar amount times 83. Orders already placed keep the totals saved at checkout. |
| Out-of-stock products at the end | The brief says to hide Add to Cart and show “Out of Stock.” This site also moves those cards to the end of the grid. In-stock cards keep the API’s order. Search uses the same sort. |
| Footer labels that are not separate shops | **Category**, **Deals**, and **New Arrivals** all go to `/products`. Help Center, Returns, Shipping, and Contact Us open **Page not found**. |
