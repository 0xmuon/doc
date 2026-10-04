# Milestone 3 — admin catalog and all orders

## Run this copy

This folder is the app as it stood at milestone 3, including `app/`, the Dockerfile, and Compose. It does not import the project root.

```powershell
cd milestones\milestone_3
docker compose up --build
```

Open `http://127.0.0.1:8013/docs`. Postgres on your machine is `localhost:5443` (user `shop`, password `shop`, database `shopping`). The project root stays on port 8000, so this copy can run beside it.


Week 3 milestone 3 is: implement admin product, category, and order access APIs.

The checks from milestone 2 already exist. These routes only declare a permission. Customers and support receive **403** `You do not have access to this action`. Admin passes.

This project does not delete a product row. Orders and cart lines point at `Products`. Deactivate sets `IsActive` to false. The public catalog hides that product. An order that already bought it still shows the name and the price that was copied at checkout.

## Routes

All of these need a bearer token.

| Method | Path | Permission | What it does |
| --- | --- | --- | --- |
| POST | `/api/admin/categories` | `catalog:manage` | Create a category. **201** |
| PUT | `/api/admin/categories/{category_id}` | `catalog:manage` | Rename it |
| POST | `/api/admin/products` | `catalog:manage` | Create a product. **201**. It starts active |
| PUT | `/api/admin/products/{product_id}` | `catalog:manage` | Update any sent field, including `is_active` |
| GET | `/api/admin/products` | `catalog:manage` | Every product, including inactive ones |
| GET | `/api/admin/orders` | `order:read:any` | Every order, newest first |

`GET /api/admin/orders` uses `order:read:any`, so support can call it too. That matches support's job of viewing orders. They still cannot create or edit products.

The role route from milestone 2 lives on the same router: `PATCH /api/admin/users/{user_id}/role`.

## Rules

- Category name and product name must be unique, compared without case. A duplicate is **409** `Category name must be unique` or `Product name must be unique`.
- A missing category or product is **404**.
- Creating a product with a category id that does not exist is **404** `Category not found`.
- Empty names, a price that is not above zero, and a negative quantity are **422**.
- Extra fields are **422**.
- Public `GET /api/products`, search, and `GET /api/products/{id}` skip inactive products. A hidden id is **404** `Product not found`, the same as a missing id.
- Adding an inactive product to a cart is **404** `Product must exist before adding to cart`.

Create body for a product:

```json
{
  "product_name": "Desk Mat",
  "description": "Large cloth mat",
  "category_id": 1,
  "price": 19.5,
  "available_quantity": 12,
  "product_url": ""
}
```

Deactivate:

```json
{ "is_active": false }
```

PUT only changes fields you send.

## Data

`Products.IsActive` is a boolean, default true. The seed catalog is inserted active. `app/db/migrate.py` adds the column on a database that already has products and sets existing rows to true. New databases get the column from the model.

`GET /api/admin/orders` reads the same `Orders` rows as the customer history. It does not invent a second order table. Each item includes `payment_status` once milestone 4 has run; older rows are marked `PAID` by the migration because they were placed before the gateway existed.

## Files

| File | Role |
| --- | --- |
| `app/routers/admin_router.py` | The HTTP surface |
| `app/services/admin_service.py` | Uniqueness, missing category, deactivate |
| `app/schemas/product_schema.py` | Create and update bodies, `is_active` on the response |
| `app/repositories/product_repository.py` | Active-only public queries, name lookups |
| `app/models/product.py` | `IsActive` |
| `app/services/order_service.py` | `list_all_orders` |

Public product reads stay on `product_router` and `product_service`. Admin writes do not go through those read functions.
