# Why the cart uses `cart_id`

A cart in a real shop is a basket. The basket has an id. The products sit inside that basket. The customer does not get a new id for every product line and then treat that line id as the cart.

The first version of this project did the second thing. `CartItems` was the only cart table. Each row had its own `CartItemID`, plus `UserID`, `ProductID`, and `Quantity`. Update and delete used that line id:

- `PUT /api/cart/update/{cart_item_id}`
- `DELETE /api/cart/remove/{cart_item_id}`

That works as a database trick. It is a weak model of a shop. There was no basket. There was no way to say "this group of products is the shopping session that has not been ordered yet." After checkout the rows were deleted, so the basket disappeared.

`cart_id` is the basket. `cart_item_id` is gone from the tables, the JSON, and the routes.

---

## What a company cart actually is

Amazon, Flipkart, and Shopify all keep the same idea, even when the column names differ.

1. A shopper has a current basket.
2. The basket has one id.
3. Products are lines inside that basket.
4. The same product added again increases quantity. It does not open a second basket.
5. Checkout closes that basket and turns it into an order.
6. The next time the shopper adds something, that is a new basket.

In this API the basket is the `Carts` row. The lines are `CartItems` rows that point at that basket.

---

## The two tables

### `Carts` — the basket

| Column | Meaning |
| --- | --- |
| `UserID` | Who owns the basket. Part of the primary key. |
| `CartID` | That user's basket number. Part of the primary key. |
| `Status` | `OPEN` or `ORDERED` |
| `CreatedAt` | When this basket was opened |

The primary key is `(UserID, CartID)`. Both numbers together identify one basket.

`CartID` is assigned in code. It is not a global database counter. The first basket for a user is `1`. After that basket is ordered, the next one is `2`, then `3`. User 4 and user 9 both start at cart `1`. Their baskets never collide because the key includes `UserID`.

`Status` has only two values:

- `OPEN` — this is the bucket of products that are not ordered yet.
- `ORDERED` — checkout already closed this basket. The lines stay on it as the record of what was in the basket.

A partial unique index allows only one `OPEN` cart per user. The database rejects a second open basket for the same shopper.

### `CartItems` — products inside the basket

| Column | Meaning |
| --- | --- |
| `UserID` | Same user as the basket. Part of the primary key. |
| `CartID` | Which basket. Part of the primary key. |
| `ProductID` | Which product. Part of the primary key. |
| `Quantity` | How many. Must be greater than 0. |

The primary key is `(UserID, CartID, ProductID)`. That is why there is no `CartItemID`. One product can appear only once inside one basket. Adding it again updates `Quantity`.

`(UserID, CartID)` is a foreign key to `Carts`. A line cannot exist in a basket that does not exist.

---

## A short example

Rudra's `UserID` is 3. He has never shopped.

1. He adds the LED Desk Lamp, quantity 2. The API creates cart `(3, 1)` with status `OPEN` and one line for the lamp.
2. He adds the lamp again with quantity 1. Cart `1` still exists. The lamp line becomes quantity 3. No second line, no second cart.
3. He adds a mug. Same cart `1`, second line.
4. He checks out. Cart `1` becomes `ORDERED`. The order stores `cart_id` 3's cart number, which is `1`. Stock goes down. The lamp and mug lines stay on cart 1.
5. `GET /api/cart/3` returns `cart_id: null` and an empty item list. The open bucket is empty because cart 1 is no longer open.
6. He adds shoes. The API creates cart `(3, 2)` with status `OPEN`.

Asha registers after Rudra already has cart 2. Asha's first add still creates cart `1` for Asha.

---

## Routes

The line is found by the user and the product inside the open cart.

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/api/cart/{user_id}` | The open basket. `cart_id` is `null` when there is no open basket. |
| GET | `/api/cart/{user_id}/summary` | Same basket, plus item count, total quantity, and total amount. |
| POST | `/api/cart/add` | Opens a basket if needed, then adds or increases a product. Returns **201**. |
| PUT | `/api/cart/update/{user_id}/{product_id}` | Sets the quantity on that product in the open basket. |
| DELETE | `/api/cart/remove/{user_id}/{product_id}` | Removes that product from the open basket. |

Add body is still `user_id`, `product_id`, and `quantity`. The response now includes `cart_id` and does not include `cart_item_id`.

Update sets the quantity. It does not add the number in the body to the old quantity.

Three empty-looking cases are different:

- The user has never added anything, or the last cart is already `ORDERED`. `cart_id` is `null`, `status` is `null`, `items` is `[]`.
- The user removed every line but has not checked out. The open cart id stays, `status` is `OPEN`, `items` is `[]`. The next add uses that same cart id.
- The user id does not exist. **404** `User not found`.

---

## Rules that stayed the same

- Quantity `0` is **422**. The schema rejects it before the service runs.
- Unknown user on add, view, update, or remove is **404** `User not found`.
- Unknown product on add is **404** `Product must exist before adding to cart`.
- Quantity above stock is **400** `Quantity cannot exceed available stock`.
- Update or remove of a product that is not in the open cart is **404**.
- Adding a product does not reduce `AvailableQuantity`. Stock drops at checkout.
- The cart line does not store a price. It reads `Products.Price` when you view the cart. Checkout copies that price onto `OrderDetails.Price`.

---

## What checkout does now

Checkout used to delete the cart rows. It now closes the basket.

In one database transaction it:

1. Loads the user's `OPEN` cart. No open cart, or an open cart with no lines, is **400** `User must have at least one cart item before checkout`.
2. Checks stock again. Another order may have bought the last units after the product was added.
3. Inserts `Orders` with this user's `CartID`.
4. Inserts `OrderDetails`. `Price` is the product price at this moment.
5. Subtracts stock.
6. Sets the cart `Status` to `ORDERED`.
7. Commits once. If anything fails before that commit, the stock, the cart, and the order all stay as they were.

The order response and the order history both include `cart_id`. That is how you can point at the basket that became the order.

`(Orders.UserID, Orders.CartID)` is a foreign key to `Carts`, and that pair is unique. One basket can become only one order, and an order cannot point at someone else's cart.

`GET /api/cart/{user_id}` does not return `ORDERED` carts. Those baskets are history. The order is the place to read them.

---

## Files that changed

| File | Change |
| --- | --- |
| `app/models/cart.py` | Added `Carts`. `CartItems` no longer has `CartItemID`. |
| `app/models/user.py` | A user has many carts. |
| `app/models/order.py` | An order stores `CartID` and must match that user's cart. |
| `app/models/__init__.py` | Imports `Cart` so the table is created. |
| `app/repositories/cart_repository.py` | Loads the open cart and calculates the next cart number for that user. |
| `app/services/cart_service.py` | Opens cart 1 on the first add, then cart 2 after checkout. |
| `app/services/order_service.py` | Closes the open cart instead of deleting its lines. |
| `app/schemas/cart_schema.py` | Responses carry `cart_id` and `status`. |
| `app/schemas/order_schema.py` | Order history and order details include `cart_id`. |
| `app/routers/cart_router.py` | Update and remove use `user_id` and `product_id`. |
| `README.md`, `ER_DIAGRAM.md`, `INTERVIEW_GUIDE.md`, `VERIFY.md` | Match this basket model. |

---

## The database has to be created again

`create_all` creates missing tables. It does not rebuild a `CartItems` table that already has `CartItemID`, and it does not add `CartID` onto old `Orders` rows.

From the project folder:

```powershell
docker compose down -v
docker compose up --build
```

`down -v` deletes the Postgres volume. Users, carts, and orders that were already saved are removed. The 4 categories and 10 products are inserted again when the API starts on an empty database.
