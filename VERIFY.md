# Verify every endpoint yourself

Do the steps in order. Later steps use ids from earlier responses.

App: `http://127.0.0.1:8000`  
Swagger: `http://127.0.0.1:8000/docs`

If the page does not load, start the stack from the project folder:

```powershell
docker compose up --build
```

In Swagger, open a route, click **Try it out**, replace the sample JSON, then **Execute**. Check the **Code** under Server response.

Write these down as you go:

| Name | Your value |
| --- | --- |
| user_id | |
| product_id (LED Desk Lamp) | |
| cart_id | |
| order_id | |

Use a new email if register returns **409**. Example: `verify.me@example.com`.

Swagger's default body fails on purpose. `"password": "string"` is too short. `"mobile": "string"` is not 10 digits. Always paste the JSON from this file.

---

## 1. App is up

`GET http://127.0.0.1:8000/`

Expect **200**:

```json
{ "message": "Online Shopping API", "docs": "/docs" }
```

This route is not listed in Swagger. Open it in the browser.

---

## 2. Categories

`GET /api/categories`

Expect **200**. Four names:

- Electronics
- Clothing
- Books
- Home and Kitchen

---

## 3. All products

`GET /api/products`

Expect **200** and **10** products. Each item has `product_id`, `product_name`, `category_name`, `price`, `available_quantity`.

Find **LED Desk Lamp**. Price is **24.75**. Stock starts at **28** unless someone already ordered it. Save its `product_id`.

---

## 4. Search

`GET /api/products/search?name=lamp`

Expect **200**. At least LED Desk Lamp. Matching ignores case.

`GET /api/products/search?category=Books`

Expect **200**. Every row has `category_name` = `Books` (Python Programming Guide, Mystery Novel).

`GET /api/products/search?category=1`

Expect **200**. `1` is a category id, so you get that category's products.

`GET /api/products/search`

No query params. Expect **200** and all products.

`GET /api/products/search?name=zzzz-no-such-product`

Expect **200** and `[]`. A miss is an empty list, not 404.

---

## 5. One product

`GET /api/products/{product_id}`

Use the lamp id. Expect **200** and `product_name` = `LED Desk Lamp`.

`GET /api/products/99999`

Expect **404**:

```json
{ "detail": "Product not found" }
```

---

## 6. Register — bad body (422)

`POST /api/users/register`

```json
{
  "name": " ",
  "email": "not-an-email",
  "password": "short",
  "mobile": "12345"
}
```

Expect **422**. `detail` mentions the name, the email, the password (minimum 8 characters), and the mobile (10 digits).

This does **not** create a user.

---

## 7. Register — success (201)

```json
{
  "name": "Rudra Shah",
  "email": "verify.me@example.com",
  "password": "secret123",
  "mobile": "9988776655"
}
```

Expect **201**:

```json
{
  "message": "User registered successfully",
  "user": {
    "user_id": 1,
    "name": "Rudra Shah",
    "email": "verify.me@example.com",
    "mobile": "9988776655"
  }
}
```

`user_id` may not be 1 if other users exist. Save whatever you get.

There is no `password` in the response.

---

## 8. Register — same email (409)

Send the same JSON again.

Expect **409**:

```json
{ "detail": "Email must be unique" }
```

---

## 9. Login — wrong password (401)

`POST /api/users/login`

```json
{
  "email": "verify.me@example.com",
  "password": "wrongpass"
}
```

Expect **401**:

```json
{ "detail": "Invalid email or password" }
```

Swagger may label 401 as Undocumented. The body above is still the correct result.

Unknown email, same password message:

```json
{
  "email": "nobody@example.com",
  "password": "secret123"
}
```

Expect **401** with the same `detail`. The API does not say whether the email exists.

---

## 10. Login — success (200)

```json
{
  "email": "verify.me@example.com",
  "password": "secret123"
}
```

Expect **200**, `message` = `Login successful`, `token_type` = `bearer`, and the same `user_id` as register. Save `access_token`.

`POST /api/auth/login` with the same body returns the same shape. Use either path.

In Swagger, click **Authorize**, paste the token only, then **Authorize** again. Cart and order calls need this. Product calls do not.

---

## 10b. Cart without a token (401)

Leave Authorize empty, or click **Logout** there.

`GET /api/cart/{user_id}`

Expect **401**:

```json
{ "detail": "Valid token is required" }
```

A made-up token such as `Authorization: Bearer not-a-real-token` is **401** `Invalid or expired token`.

Turn Authorize back on before the cart steps below. If the path or body `user_id` is not your token's user, expect **403** `You can only access your own cart`.

---

## 11. Cart — another user's id (403)

Authorize with your token, then `GET /api/cart/99999`.

Expect **403**:

```json
{ "detail": "You can only access your own cart" }
```

`GET /api/cart/99999/summary` is the same **403**. The API does not look up user 99999 when the token belongs to someone else.

---

## 12. Cart — empty (200)

`GET /api/cart/{user_id}`

Expect **200**:

```json
{ "user_id": 1, "cart_id": null, "status": null, "items": [] }
```

`cart_id` is null until the first add. There is no separate cart item id.

`GET /api/cart/{user_id}/summary`

Expect **200**, `cart_id` null, `distinct_items` 0, `total_quantity` 0, `total_amount` 0, `items` empty.

---

## 13. Add to cart — bad quantity (422)

`POST /api/cart/add`

```json
{
  "user_id": 1,
  "product_id": 1,
  "quantity": 0
}
```

Use your real `user_id` and lamp `product_id`. Expect **422** because quantity must be greater than 0.

---

## 14. Add to cart — wrong user or missing product

Unknown user, while Authorize has your token:

```json
{
  "user_id": 99999,
  "product_id": 1,
  "quantity": 1
}
```

Expect **403**:

```json
{ "detail": "You can only access your own cart" }
```

Unknown product, with your real `user_id`:

```json
{
  "user_id": 1,
  "product_id": 99999,
  "quantity": 1
}
```

Expect **404**:

```json
{ "detail": "Product must exist before adding to cart" }
```

---

## 15. Add to cart — success (201)

```json
{
  "user_id": 1,
  "product_id": 9,
  "quantity": 2
}
```

Replace ids. Expect **201**. Check:

- `quantity` is 2
- `product_name` is LED Desk Lamp
- `unit_price` is 24.75
- `line_total` is 49.5
- `available_quantity` is still the old stock (add does not reduce stock)
- `cart_id` is **1** for this user's first basket. Another user also starts at 1

There is no `cart_item_id`. The line is this cart plus the product.

---

## 16. Add the same product again

Send the same body with `"quantity": 1`.

Expect **201**. `quantity` is now **3** (2 + 1). There is still one line in cart **1**, not a second cart. `line_total` is **74.25**. `cart_id` is still 1.

---

## 17. Add more than stock (400)

```json
{
  "user_id": 1,
  "product_id": 9,
  "quantity": 999
}
```

Expect **400**:

```json
{ "detail": "Quantity cannot exceed available stock" }
```

The cart quantity stays 3.

---

## 18. View cart and summary

`GET /api/cart/{user_id}`

Expect one item, quantity 3.

`GET /api/cart/{user_id}/summary`

Expect:

- `distinct_items` = 1
- `total_quantity` = 3
- `total_amount` = 74.25

---

## 19. Update cart — product not in the open cart (404)

`PUT /api/cart/update/{user_id}/99999`

```json
{ "quantity": 1 }
```

Use your real `user_id`. Expect **404**:

```json
{ "detail": "Cart item must exist before update" }
```

---

## 20. Update cart — success (200)

`PUT /api/cart/update/{user_id}/{product_id}`

```json
{ "quantity": 1 }
```

Expect **200**. `quantity` is 1. `line_total` is 24.75. `cart_id` is still 1.

This **sets** the quantity. It does not add 1 to the old quantity.

Summary again: `total_quantity` 1, `total_amount` 24.75.

---

## 21. Update above stock (400)

```json
{ "quantity": 999 }
```

Expect **400**: `Quantity cannot exceed available stock`. Quantity stays 1.

---

## 22. Checkout — bad payment (422)

`POST /api/orders/checkout`

```json
{
  "user_id": 1,
  "payment_method": "CASH"
}
```

Expect **422**. Allowed values are `COD`, `CARD`, `UPI`, `NET_BANKING`.

---

## 23. Checkout — success (201)

Set quantity to 2 first with `PUT /api/cart/update/{user_id}/{product_id}` and `{ "quantity": 2 }`, so the total is easy to check (49.5).

```json
{
  "user_id": 1,
  "payment_method": "upi"
}
```

Expect **201**:

- `message` = `Order placed successfully`
- `payment_method` = `UPI` (lower case in the request is stored upper case)
- `total_amount` = 49.5
- `cart_id` = 1
- one line, `quantity` 2, `price` 24.75, `line_total` 49.5

Save `order_id`.

Then check:

- `GET /api/cart/{user_id}` → `cart_id` is `null`, `status` is `null`, `items` is `[]`. Cart 1 is ordered, so it is no longer the open basket.
- `GET /api/products/{lamp_id}` → `available_quantity` is 2 less than before checkout

The client does not send the total. The server calculates it.

---

## 24. Checkout — someone else's user or empty cart (403 / 400)

Someone else's user id, with your token:

```json
{
  "user_id": 99999,
  "payment_method": "COD"
}
```

Expect **403**: `You can only access your own orders`.

`user_id` of `0` is **422**: `User id must be greater than 0`.

Empty cart (same user you just checked out):

Send the same checkout body again.

Expect **400**:

```json
{ "detail": "User must have at least one cart item before checkout" }
```

---

## 25. Order history

`GET /api/orders/{user_id}`

Expect **200** and a list. The newest order is first. It has `order_id`, `cart_id` 1, `order_date`, `payment_method` `UPI`, `total_amount` 49.5. History does not include line items.

`GET /api/orders/me`

Expect **200** and the same list as history. This path uses the token, so there is no user id in the URL.

`GET /api/orders/99999`

Expect **403**: `You can only access your own orders`.

---

## 26. Order details

`GET /api/orders/details/{order_id}`

Expect **200**. `cart_id` is 1. Same total, and `items` contains the lamp line with the price copied at checkout (24.75).

`GET /api/orders/details/99999`

Expect **404**:

```json
{ "detail": "Order not found" }
```

---

## 27. Remove from cart

Add another product so there is something to delete.

`POST /api/cart/add`

```json
{
  "user_id": 1,
  "product_id": 1,
  "quantity": 1
}
```

Use a real product id from the product list. Expect **201**. `cart_id` is **2**, because cart 1 was already ordered.

`DELETE /api/cart/remove/{user_id}/{product_id}`

Expect **200**:

```json
{ "message": "Item removed from cart" }
```

`GET /api/cart/{user_id}` no longer shows that line. The open cart id stays 2. If that was the only line, `items` is `[]` and `status` is still `OPEN`.

`DELETE /api/cart/remove/{user_id}/99999`

Expect **404**:

```json
{ "detail": "Cart item must exist before delete" }
```

---

## 28. Other payment methods

Add one item, then checkout. Repeat so you try each method. Each must return **201** and store the method in upper case:

| Send | Stored |
| --- | --- |
| `COD` | `COD` |
| `card` | `CARD` |
| `NET_BANKING` | `NET_BANKING` |

You already checked `upi` → `UPI`.

---

## Checklist

- [ ] Home page 200
- [ ] 4 categories
- [ ] 10 products
- [ ] Search by name, by category name, by category id
- [ ] Product details 200 and missing product 404
- [ ] Register 422 on a bad body
- [ ] Register 201, no password in the response
- [ ] Duplicate email 409
- [ ] Wrong password and unknown email both 401
- [ ] Login 200 and save access_token
- [ ] Cart without a token is 401
- [ ] Cart for another user id is 403
- [ ] Empty cart 200
- [ ] Quantity 0 is 422
- [ ] Missing product on add is 404
- [ ] Add for another user id is 403
- [ ] Search with no match returns `[]`
- [ ] Checkout for another user is 403
- [ ] First add returns cart_id 1, and the add after checkout returns cart_id 2
- [ ] Over stock 400
- [ ] Summary matches price times quantity
- [ ] Update missing item 404
- [ ] Update sets quantity
- [ ] Bad payment 422
- [ ] Checkout 201, cart cleared, stock reduced
- [ ] Second checkout 400
- [ ] Order history 200
- [ ] Order details 200 and missing order 404
- [ ] Remove item 200 and remove missing item 404
