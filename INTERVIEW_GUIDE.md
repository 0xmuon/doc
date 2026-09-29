# Online shopping API — study guide

This file explains the project the way you would explain it in an interview. Read it once end to end, then use the question section at the bottom to practice out loud.

The app is a backend only. There is no website UI. A client (Swagger, Postman, or a future frontend) sends HTTP requests, and this API talks to PostgreSQL.

Swagger is already generated: open `http://127.0.0.1:8000/docs` after the app is running.

---

## 1. What to say in 30 seconds

> I built the user module of an online shopping API with FastAPI and PostgreSQL. A user can register and log in, browse and search products, manage a cart, and place an order. The code is split into routers, services, repositories, and SQLAlchemy models. Input is checked with Pydantic. Business mistakes (empty cart, not enough stock, duplicate email) are custom exceptions that become JSON. Passwords are stored as a salted hash, not plain text. Login checks the Users table and returns a JWT. Cart and order routes require that bearer token, and the user id in the request must match the token.

---

## 2. How a request moves

Every successful call follows the same path.

```
client
  -> router          (url, method, status code)
  -> pydantic schema (shape and format of the body)
  -> service         (business rules)
  -> repository      (sql)
  -> postgresql
```

Example: `POST /api/cart/add`

1. FastAPI matches the path to `add_to_cart` in `app/routers/cart_router.py`.
2. `Depends(get_db)` opens one database session for this request.
3. `CartAddRequest` checks that `user_id`, `product_id`, and `quantity` are positive integers. If `quantity` is 0, FastAPI stops here with **422**. The service never runs.
4. `cart_service.add_item` checks that the user exists, the product exists, and the quantity is not above stock.
5. `cart_repository` finds the user's open cart, or creates cart id 1, then inserts or updates a line in that cart and commits.
6. The service builds a response. The router returns **201**.

If the service raises `NotFoundException`, `main.py` turns it into `{"detail": "..."}` with status **404**. The router does not contain that if/else.

---

## 3. Folder map

```
app/
  main.py                 starts the app, creates tables, handles errors
  models/                 table classes (user, category, product, cart, order)
  db/
    base.py               shared sqlalchemy base class
    session.py            engine, session, get_db
    seed.py               sample categories and products, inserted once
  schemas/                pydantic request and response models
  repositories/           sql only
  services/               rules only
  routers/                http only
  utils/
    exceptions.py         400, 401, 404, 409
    helpers.py            password hash, money rounding, payment methods
```

Models sit in `app/models`, not inside `db`. `db` only holds the connection and the seed.

There is no separate category router. `GET /api/categories` lives in `product_router.py` because the suggested file list only had user, product, cart, and order files. The category *table* still exists as `app/models/category.py`.

### What each layer is allowed to do

| Layer | Does | Does not |
| --- | --- | --- |
| Router | URL, status code, call the service | stock checks, sql |
| Schema | "is this email shaped like an email?" | "is this email already used?" |
| Service | "is stock enough? is the cart empty?" | write the SQL string |
| Repository | select, insert, update, delete | decide the error message |
| Model | column names and relationships | http |

Interview line: **format checks are 422 from Pydantic. Business checks are 400, 401, 404, or 409 from the service.**

---

## 4. Concepts you should be able to explain

### API

An API is a set of urls a program can call. This one uses HTTP and JSON.

- **GET** reads data. It should not change the database.
- **POST** creates something (user, cart line, order).
- **PUT** replaces a value (cart quantity is set to the new number, not added).
- **DELETE** removes a row.

### JSON

The body of a request and the answer are JSON objects. Python dicts are converted to JSON by FastAPI.

### FastAPI and Uvicorn

FastAPI is the framework that maps urls to Python functions and builds `/docs`. Uvicorn is the server that actually listens on port 8000. FastAPI does not listen by itself.

```powershell
uvicorn app.main:app --reload
```

`app.main:app` means: in the file `app/main.py`, use the variable named `app`.

### Path, query, and body

- **Path** is inside the url: `/api/products/3` means `product_id` is 3.
- **Query** is after `?`: `/api/products/search?name=lamp&category=Books`.
- **Body** is the JSON sent with POST or PUT. It is not visible in the url.

`/api/products/search` is declared **before** `/api/products/{product_id}`. If the order were reversed, the word `search` would be treated as a product id and the search route would never run. Same idea for `/api/orders/details/{order_id}` before `/api/orders/{user_id}`.

### Pydantic schema

A schema is a class that describes JSON. FastAPI reads the body and builds that class. If a field is missing or the wrong type, the function is not called.

`EmailStr` means the value must look like `name@domain.com`. `Field(gt=0)` means the number must be greater than 0. `@field_validator` is extra logic, such as "name cannot be only spaces" or "mobile must be 10 digits".

`UserResponse` does **not** include `password`. That is on purpose. `model_config = ConfigDict(from_attributes=True)` lets Pydantic read a SQLAlchemy object (`user.email`) instead of only a dict.

### SQLAlchemy model vs schema

People mix these up. Say this:

> The model is the database table. The schema is the JSON contract. They are separate so a password column can exist in the table but never appear in the API response.

`User.user_id` in Python is column `"UserID"` in PostgreSQL. The Python name is what the code uses. The string in `mapped_column` is the real column name.

### Session and `get_db`

`create_engine` knows how to talk to PostgreSQL. `SessionLocal` makes short conversations with the database. `get_db` is a FastAPI dependency:

```python
def register(payload: UserCreate, db: Session = Depends(get_db)):
```

For each request FastAPI calls `get_db`, gives that session to the function, and closes it at the end. If the request crashes, `get_db` rolls the session back so a half-written change is not kept.

### Dependency injection

`Depends(get_db)` means "please give me a database session; I do not create it myself." That keeps routers easy to test and makes sure every request gets its own session.

### ORM and relationships

You do not write `SELECT * FROM Products` in the routers. A `Product` object is a row. `product.category.category_name` works because the model says a product belongs to one category.

```
Users 1 --- many Carts
Carts 1 --- many CartItems
Users 1 --- many Orders
Categories 1 --- many Products
Products 1 --- many CartItems
Products 1 --- many OrderDetails
Orders 1 --- many OrderDetails
Carts 1 --- zero or one Order
```

A user can have many carts over time. Only one of them is `OPEN`. `CartID` starts at 1 for every user: the first basket is 1, the basket after the first checkout is 2. Lines inside a cart are unique on `ProductID`. Adding the same product again increases `Quantity`. There is no `CartItemID`.

### Commit, flush, rollback

- **flush** sends SQL but the transaction is still open. Checkout does this so the new order gets an `OrderID` before the line items are inserted.
- **commit** makes the change permanent.
- **rollback** throws the change away.

Checkout inserts the order, inserts every line, reduces stock, and marks the open cart as `ORDERED`, then commits **once**. The lines stay on that cart as the basket that was bought. If anything fails before that commit, none of those changes stay. That is one transaction.

### Why the order stores its own price

The cart does not store a price. It reads `Products.Price` at that moment. When the user checks out, that price is copied onto `OrderDetails.Price`. If the product price changes tomorrow, the old order still shows what the customer paid.

### Password hashing

The `Password` column stores `salt$hash`, not `secret123`. `hash_password` makes a random salt and runs PBKDF2-HMAC-SHA256. `verify_password` splits the salt back out and hashes the typed password the same way. Two users with the same password still get different stored values because the salt differs.

Login does not say "email not found" versus "wrong password". Both return **401** `Invalid email or password`. That stops someone from discovering which emails are registered.

Login checks the Users table, then `create_access_token` puts the user id in the JWT `sub` claim. The password is not inside the token. `POST /api/users/login` and `POST /api/auth/login` both return `access_token` and `token_type` `bearer`.

Cart and order routes use `get_current_user`. A missing or bad token is **401**. A valid token for a different `user_id` than the path or body is **403**. Product browse does not need a token.

### CORS

`CORSMiddleware` with `allow_origins=["*"]` lets a browser page on another origin call this API. Swagger on the same host does not need it. It is there so a future frontend can call the API.

### Seed data

On startup, if the `Categories` table is empty, `seed.py` inserts 4 categories and 10 products. If categories already exist, it does nothing. That is why restarting the app does not duplicate products.

Categories: Electronics, Clothing, Books, Home and Kitchen.

### Docker

`docker compose up --build` starts two containers.

- `db` is Postgres 17. From your laptop the port is **5433**. Inside the Docker network the host name is `db` and the port is **5432**.
- `api` is this FastAPI app on port **8000**. It reads `DATABASE_URL` from `.env`.

If you run `uvicorn` on your machine, `DATABASE_URL` must use `localhost` and port `5433`. If you run inside Compose, it must use host `db` and port `5432`.

---

## 5. Tables

| Table | Important columns | Rule |
| --- | --- | --- |
| Users | UserID, Name, Email, Password, Mobile | Email is unique |
| Categories | CategoryID, CategoryName | CategoryName is unique |
| Products | ProductID, ProductName, Description, CategoryID, Price, AvailableQuantity, ProductUrl | ProductName is unique. CategoryID is a foreign key |
| Carts | UserID + CartID, Status, CreatedAt | one open basket per user. CartID starts at 1 for each user |
| CartItems | UserID + CartID + ProductID, Quantity | one line per product inside a cart. Quantity must be > 0 |
| Orders | OrderID, UserID, CartID, OrderDate, PaymentMethod, TotalAmount | CartID is the basket that was checked out. TotalAmount is calculated by the server |
| OrderDetails | OrderDetailID, OrderID, ProductID, Quantity, Price | Price is the unit price at checkout |

Payment methods stored on the order: `COD`, `CARD`, `UPI`, `NET_BANKING`. The API uppercases the value, so `"upi"` becomes `UPI`.

---

## 6. Workflows

Use these bodies in Swagger. The default sample `"password": "string"` fails on purpose: the password must be at least 8 characters, and mobile must be 10 digits.

### 6.1 Register

`POST /api/users/register` → **201**

```json
{
  "name": "Rudra Shah",
  "email": "rudra.shop@example.com",
  "password": "secret123",
  "mobile": "9988776655"
}
```

What happens:

1. Schema trims the name, lowercases the email, checks password length and mobile.
2. Service looks up the email. If it exists, **409** `Email must be unique`.
3. Password is hashed. A `Users` row is inserted.
4. Response has `message` and `user`. No password field.

Same email at the same time can also hit the database unique constraint. That `IntegrityError` is caught and returned as the same 409.

### 6.2 Login

`POST /api/users/login` → **200**

```json
{
  "email": "rudra.shop@example.com",
  "password": "secret123"
}
```

Service loads the user by email and calls `verify_password`. Success returns the user plus `access_token`. Failure is **401**, whether the email is unknown or the password is wrong. `POST /api/auth/login` does the same check and returns the same body.

In Swagger, click **Authorize**, paste only the token (no `Bearer` word), then call cart or order routes.

### 6.3 Browse

| Call | Result |
| --- | --- |
| `GET /api/categories` | the 4 category names |
| `GET /api/products` | all 10 products, each with `category_name` and `price` |
| `GET /api/products/3` | one product, or **404** `Product not found` |
| `GET /api/products/search?name=lamp` | names containing "lamp", case does not matter |
| `GET /api/products/search?category=Books` | only that category |
| `GET /api/products/search?category=1` | category id, because the value is all digits |

`name` and `category` are optional. Search joins the category so the response can include `category_name` without a second query per product (`joinedload`).

### 6.4 Cart

`POST /api/cart/add` → **201**

```json
{
  "user_id": 1,
  "product_id": 9,
  "quantity": 2
}
```

Rules, in order:

1. Quantity must be > 0, or **422** (schema).
2. User must exist, or **404** `User not found`.
3. Product must exist, or **404** `Product must exist before adding to cart`.
4. If the open cart already has that product, new quantity = old quantity + requested quantity.
5. That total must be `<= AvailableQuantity`, or **400** `Quantity cannot exceed available stock`.
6. Insert or update the line inside the open cart, then return the line with `cart_id`, `unit_price`, and `line_total`.

The first add for a user creates cart `1` with status `OPEN`. A later add, before checkout, stays in that same cart. After checkout, the next add creates cart `2`. Another user also starts at cart `1`.

`GET /api/cart/{user_id}` returns the open basket. If the user has never added anything, or the last cart was already ordered, `cart_id` is `null` and `items` is `[]`. That is not a 404. An open cart whose lines were all removed still has its `cart_id` and status `OPEN`, with `items` empty.

`GET /api/cart/{user_id}/summary` adds `distinct_items`, `total_quantity`, and `total_amount`.

`PUT /api/cart/update/{user_id}/{product_id}` sets quantity to the number in the body. It does not add. A product that is not in the open cart is **404** `Cart item must exist before update`.

`DELETE /api/cart/remove/{user_id}/{product_id}` returns `{"message": "Item removed from cart"}`. Missing product is **404**.

The summary route is `/cart/{user_id}/summary`. It is registered before `/cart/{user_id}` so `summary` is not parsed as a user id.

### 6.5 Checkout

`POST /api/orders/checkout` → **201**

```json
{
  "user_id": 1,
  "payment_method": "upi"
}
```

The client does **not** send the total. The server calculates it.

1. Payment method must be one of the four allowed values, or **422** from the schema (`"CASH"` fails here).
2. User must exist, or **404**.
3. Cart must have at least one line, or **400** `User must have at least one cart item before checkout`.
4. Each line quantity must still be `<=` current stock, or **400** `Ordered quantity must not exceed available quantity`. Stock is checked again because another order may have reduced it after the item was added.
5. `TotalAmount` = sum of (current price × quantity), rounded to 2 decimals.
6. Insert `Orders` with that `cart_id`, insert `OrderDetails` with the copied unit price, subtract stock, set the cart status to `ORDERED`, commit once.
7. Response includes the order, its `cart_id`, and its lines.

`GET /api/orders/{user_id}` is history: id, cart id, date, payment method, total. No line items.

`GET /api/orders/details/{order_id}` is the full order including lines. Unknown id is **404** `Order not found`.

After a successful checkout there is no open cart, so a second checkout returns **400**. The ordered cart is kept, with status `ORDERED`. It is not what `GET /api/cart/{user_id}` returns.

Worked example: LED Desk Lamp is 24.75. Quantity 3. Summary and order total are **74.25**. Payment method stored as `CARD` if the body said `"card"`.

---

## 7. Error handling

There are three layers of errors.

### A. Pydantic — status 422

FastAPI does this before your service. You do not write the 422 yourself.

| Bad input | Message |
| --- | --- |
| `"name": "   "` | Name cannot be empty |
| `"email": "not-an-email"` | email format error |
| `"password": "string"` | Password must meet minimum length of 8 characters |
| `"mobile": "string"` or `"12345"` | Mobile must be numeric and of valid length (10 digits) |
| cart `"quantity": 0` | greater than 0 |
| `"payment_method": "CASH"` | Payment method must be valid |

Response shape:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "Value error, Password must meet minimum length of 8 characters"
    }
  ]
}
```

This is why Swagger's sample body fails. `"password": "string"` is 6 characters. `"mobile": "string"` is not 10 digits. Change those two fields and register works.

### B. Service exceptions — 400, 401, 404, 409

Defined in `app/utils/exceptions.py`. `main.py` catches `AppException` and returns:

```json
{ "detail": "Email must be unique" }
```

| Class | Status | When |
| --- | --- | --- |
| `AppException` | 400 | stock too high, empty cart, bad payment if it reaches the service |
| `UnauthorizedException` | 401 | login failed |
| `NotFoundException` | 404 | user, product, cart line, or order does not exist |
| `ConflictException` | 409 | email already registered |

401 is marked "Undocumented" in Swagger because the route's `responses` list only shows 200 and 422. The handler still returns 401. That is expected, not a crash.

### C. Unexpected errors — 500

Any other exception is logged on the server and the client only sees:

```json
{ "detail": "Internal server error" }
```

The real stack trace stays in the container logs. The user does not see table names or SQL.

### What to say if they ask "where is try/except?"

> Format errors are raised by Pydantic and FastAPI converts them. Business errors are raised in services and one handler in `main.py` converts them. Repositories do not catch them. `get_db` rolls back the session if the request fails. Checkout uses a single commit so a failure does not leave an order without reducing stock, or reduce stock without an order.

---

## 8. Status codes used in this project

| Code | Meaning in this app |
| --- | --- |
| 200 | read, login, cart update, cart delete |
| 201 | user created, cart line created, order created |
| 400 | business rule failed |
| 401 | login failed |
| 404 | row not found |
| 409 | unique email clash |
| 422 | body failed schema checks |
| 500 | bug we did not expect |

---

## 9. Startup, in order

1. Uvicorn imports `app.main:app`.
2. Importing `app.models` registers every table on `Base.metadata`.
3. `lifespan` runs `create_all`, which creates missing tables. It does not delete old ones.
4. `seed_database` inserts categories and products only if no category exists.
5. The process listens on port 8000.
6. A request arrives, `get_db` opens a session, the route runs, the session closes.

PostgreSQL check constraints say `"Quantity" > 0` with quotes. Unquoted `Quantity` would be folded to lowercase `quantity` and table creation would fail, because the real column is `"Quantity"`.

---

## 10. Questions they may ask, with a short answer

**Why FastAPI?** It gives typed routes, automatic validation, and Swagger from the same code.

**Why layers?** A router change should not rewrite SQL. A stock rule should live in one service, not be copied into every route.

**Why not return the password?** The hash is still a secret. The response model simply has no password field.

**Why hash instead of encrypt?** A hash is one way. We never need the original password back. Login hashes the attempt and compares.

**What is a foreign key?** `Products.CategoryID` must point at a real `Categories.CategoryID`. The database rejects a product whose category does not exist.

**What is a primary key?** The id that identifies one row. `UserID`, `ProductID`, and `OrderID` are generated by the database. `CartID` is different: it is numbered per user, starting at 1, and together with `UserID` it identifies one basket.

**Why does cart id start at 1 for every user?** A cart is that shopper's basket, not a global ticket number. User 4 and user 9 both get cart 1 for their first basket. Checkout closes cart 1. The next basket for that same user is cart 2. Lines are found by product inside the open cart, so there is no `CartItemID`.

**Difference between 400 and 422?** 422 means the JSON itself is invalid. 400 means the JSON is valid but the business rule failed (stock, empty cart).

**Difference between 401 and 404 on login?** We use 401 for both unknown email and wrong password so we do not reveal which emails exist.

**Difference between 401 and 403 on cart?** 401 means the token is missing, expired, or fake. 403 means the token is valid, but the `user_id` in the path or body is a different person.

**Why 409 for duplicate email?** 409 means the request conflicts with current data. 400 would also be understood, but 409 is the usual choice for a unique-key clash.

**Can the client send the order total?** No. The server multiplies price by quantity. Otherwise a client could send a total of 1.

**What if two people buy the last item?** Checkout reads stock again inside the same transaction and rejects the order if quantity is above `AvailableQuantity`. The simple version does not use `SELECT FOR UPDATE`. If they ask about race conditions, say the re-check is there, and a stricter version would lock the product row.

**Why is search a query string?** Filters are optional. A body on GET is unusual. `?name=&category=` matches the case study.

**What does `joinedload` do?** It fetches the related category (or product) in the same query so the code can use `product.category.category_name` without one extra query per row.

**What is middleware?** Code that runs around every request. CORS middleware adds headers so browsers on other origins are allowed to call the API.

**What is OpenAPI?** The machine-readable description of the routes. FastAPI builds it. Swagger UI is the web page on `/docs` that reads that description.

**How do you run it?** `docker compose up --build`. API on port 8000, Postgres on localhost port 5433.

**What would you add next?** Role checks so an admin can manage products, and pagination on the product list. Say this only if they ask what is missing. Do not apologize for the case study scope.

---

## 11. One full story you can narrate

1. App starts, tables are created, 4 categories and 10 products are inserted.
2. Rudra registers with email `rudra.shop@example.com`, password `secret123`, mobile `9988776655`. The stored password is a salt plus hash.
3. He logs in. The API finds that email and the hash matches. The response includes his user and an `access_token`. Later cart and order calls send `Authorization: Bearer` plus that token.
4. He searches `name=lamp` and gets the LED Desk Lamp.
5. He adds quantity 2. The line total is 24.75 × 2.
6. He updates the line to quantity 3. Summary total is 74.25. Stock is still unchanged.
7. He checks out with `CARD`. An order row and one detail row are written. The order stores `cart_id` 1. The detail price is 24.75, not whatever the lamp costs later. Stock drops by 3. Cart 1 is marked `ORDERED`.
8. Order history shows that order. Order details show the lamp line. A second checkout fails because there is no open cart. The next add opens cart 2.

If any step used a bad body, he would see 422 before those rules run. If the lamp id did not exist, he would see 404 from the cart service. If he asked for 999 units, he would see 400.
