"""week 3 paths against the sqlite app.cart still uses product id,not a line id."""

import os

from tests.helpers import auth, login, register


def test_browse_is_public_and_login_returns_role(client):
    products = client.get("/api/products")
    assert products.status_code == 200
    assert len(products.json()) == 10
    categories = client.get("/api/categories")
    assert categories.status_code == 200
    assert len(categories.json()) == 4
    assert "X-Request-ID" in categories.headers

    register(client, "shopper1@example.com")
    token = login(client, "shopper1@example.com")
    body = client.post("/api/users/login", json={"email": "shopper1@example.com", "password": "secret123"}).json()
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "CUSTOMER"
    assert token

    extra = client.post(
        "/api/users/register",
        json={
            "name": "Nope",
            "email": "nope-role@example.com",
            "password": "secret123",
            "mobile": "9988776655",
            "role": "ADMIN",
        },
    )
    assert extra.status_code == 422


def test_cart_requires_token_and_own_user(client):
    missing = client.get("/api/cart/1")
    assert missing.status_code == 401
    register(client, "shopper2@example.com")
    token = login(client, "shopper2@example.com")
    user_id = client.post(
        "/api/auth/login", json={"email": "shopper2@example.com", "password": "secret123"}
    ).json()["user"]["user_id"]
    own = client.get(f"/api/cart/{user_id}", headers=auth(token))
    assert own.status_code == 200
    other = client.get(f"/api/cart/{user_id + 50}", headers=auth(token))
    assert other.status_code == 403


def test_support_can_read_orders_but_not_cart_or_catalog(client):
    support = login(client, "support@example.com", "support12345")
    admin = login(client, "admin@example.com", "admin12345")
    register(client, "shopper3@example.com")
    customer = login(client, "shopper3@example.com")
    customer_id = client.post(
        "/api/auth/login", json={"email": "shopper3@example.com", "password": "secret123"}
    ).json()["user"]["user_id"]

    cart = client.get(f"/api/cart/{customer_id}", headers=auth(support))
    assert cart.status_code == 403
    history = client.get(f"/api/orders/{customer_id}", headers=auth(support))
    assert history.status_code == 200
    blocked = client.post(
        "/api/admin/categories",
        json={"category_name": "Support Should Fail"},
        headers=auth(support),
    )
    assert blocked.status_code == 403

    created = client.post(
        "/api/admin/categories",
        json={"category_name": "Audio Gear"},
        headers=auth(admin),
    )
    assert created.status_code == 201, created.text
    duplicate = client.post(
        "/api/admin/categories",
        json={"category_name": "audio gear"},
        headers=auth(admin),
    )
    assert duplicate.status_code == 409

    hidden = client.put(
        "/api/admin/products/1",
        json={"is_active": False},
        headers=auth(admin),
    )
    assert hidden.status_code == 200
    assert hidden.json()["is_active"] is False
    assert client.get("/api/products/1").status_code == 404
    names = [row["product_name"] for row in client.get("/api/products").json()]
    assert "Wireless Headphones" not in names
    # put it back so later tests can buy product 1 if they run after this
    client.put("/api/admin/products/1", json={"is_active": True}, headers=auth(admin))
    assert customer


def test_checkout_payment_and_retry(client, monkeypatch):
    register(client, "buyer@example.com")
    token = login(client, "buyer@example.com")
    user_id = client.post(
        "/api/auth/login", json={"email": "buyer@example.com", "password": "secret123"}
    ).json()["user"]["user_id"]
    added = client.post(
        "/api/cart/add",
        json={"user_id": user_id, "product_id": 2, "quantity": 1},
        headers=auth(token),
    )
    assert added.status_code == 201, added.text
    assert added.json()["cart_id"] == 1

    monkeypatch.setenv("PAYMENT_FORCE", "fail")
    failed = client.post(
        "/api/orders/checkout",
        json={"user_id": user_id, "payment_method": "upi"},
        headers=auth(token),
    )
    assert failed.status_code == 201, failed.text
    body = failed.json()
    assert body["order"]["payment_status"] == "FAILED"
    assert body["order"]["cart_id"] == 1
    order_id = body["order"]["order_id"]

    monkeypatch.setenv("PAYMENT_FORCE", "ok")
    paid = client.post("/api/payments/process", json={"order_id": order_id}, headers=auth(token))
    assert paid.status_code == 200, paid.text
    assert paid.json()["payment_status"] == "PAID"
    again = client.post("/api/payments/process", json={"order_id": order_id}, headers=auth(token))
    assert again.status_code == 200
    assert again.json()["payment_status"] == "PAID"

    note = client.post("/api/notifications/send", json={"order_id": order_id}, headers=auth(token))
    assert note.status_code == 200
    assert note.json()["message"] == "Notification queued"

    admin = login(client, "admin@example.com", "admin12345")
    all_orders = client.get("/api/admin/orders", headers=auth(admin))
    assert all_orders.status_code == 200
    assert any(row["order_id"] == order_id for row in all_orders.json())

    os.environ["PAYMENT_FORCE"] = "ok"


def test_role_change_applies_on_the_next_call(client):
    registered = register(client, "promote@example.com", name="Promote")
    user_id = registered["user"]["user_id"]
    admin = login(client, "admin@example.com", "admin12345")
    admin_id = client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "admin12345"}
    ).json()["user"]["user_id"]
    own = client.patch(
        f"/api/admin/users/{admin_id}/role",
        json={"role": "CUSTOMER"},
        headers=auth(admin),
    )
    assert own.status_code == 403
    promoted = client.patch(
        f"/api/admin/users/{user_id}/role",
        json={"role": "SUPPORT"},
        headers=auth(admin),
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "SUPPORT"
    token = login(client, "promote@example.com")
    denied = client.post(
        "/api/cart/add",
        json={"user_id": user_id, "product_id": 2, "quantity": 1},
        headers=auth(token),
    )
    assert denied.status_code == 403
