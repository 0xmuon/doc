"""service rules that do not need the whole api story.argon2 is checked with no database."""

import pytest

from app.utils import hash_password, verify_password
from tests.helpers import auth, login, register


def test_new_passwords_are_argon2():
    stored = hash_password("secret123")
    assert stored.startswith("$argon2")
    assert verify_password("secret123", stored)
    assert not verify_password("other-password", stored)


@pytest.mark.integration
def test_auth_me_returns_the_token_user(client):
    register(client, "me@example.com")
    token = login(client, "me@example.com")
    me = client.get("/api/auth/me", headers=auth(token))
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "me@example.com"
    assert body["is_active"] is True
    assert "password" not in body


@pytest.mark.integration
def test_inactive_user_cannot_login(client):
    from app.db import SessionLocal
    from app.models import User

    register(client, "paused@example.com")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "paused@example.com").one()
        user.is_active = False
        db.commit()
    finally:
        db.close()
    refused = client.post("/api/auth/login", json={"email": "paused@example.com", "password": "secret123"})
    assert refused.status_code == 401


@pytest.mark.integration
def test_same_product_stays_one_cart_line(client):
    register(client, "cartline@example.com")
    token = login(client, "cartline@example.com")
    user_id = client.get("/api/auth/me", headers=auth(token)).json()["user_id"]
    first = client.post(
        "/api/cart/add",
        json={"user_id": user_id, "product_id": 2, "quantity": 1},
        headers=auth(token),
    )
    second = client.post(
        "/api/cart/add",
        json={"user_id": user_id, "product_id": 2, "quantity": 1},
        headers=auth(token),
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["cart_item_id"] == second.json()["cart_item_id"]
    assert second.json()["quantity"] == 2
    cart = client.get(f"/api/cart/{user_id}", headers=auth(token)).json()
    assert len(cart["items"]) == 1


@pytest.mark.integration
def test_failed_payment_puts_stock_back(client, monkeypatch):
    before = client.get("/api/products/2").json()["available_quantity"]
    register(client, "stock@example.com")
    token = login(client, "stock@example.com")
    user_id = client.get("/api/auth/me", headers=auth(token)).json()["user_id"]
    added = client.post(
        "/api/cart/add",
        json={"user_id": user_id, "product_id": 2, "quantity": 2},
        headers=auth(token),
    )
    assert added.status_code == 201
    monkeypatch.setenv("PAYMENT_FORCE", "fail")
    failed = client.post(
        "/api/orders/checkout",
        json={"user_id": user_id, "payment_method": "CARD"},
        headers=auth(token),
    )
    assert failed.status_code == 201, failed.text
    order = failed.json()["order"]
    assert order["payment_status"] == "FAILED"
    assert order["order_status"] == "PAYMENT_FAILED"
    assert order["order_number"].startswith("ORD-")
    assert order["failure_reason"]
    assert client.get("/api/products/2").json()["available_quantity"] == before


@pytest.mark.integration
def test_delete_product_only_deactivates_it(client):
    admin = login(client, "rudraksh@example.com", "rudraksh1234")
    created = client.post(
        "/api/admin/products",
        json={
            "sku": "test-009",
            "product_name": "Service Lamp",
            "description": "A lamp used by the service test",
            "category_id": 1,
            "price": "12.50",
            "available_quantity": 4,
        },
        headers=auth(admin),
    )
    assert created.status_code == 201, created.text
    product_id = created.json()["product_id"]
    assert created.json()["sku"] == "TEST-009"
    removed = client.delete(f"/api/admin/products/{product_id}", headers=auth(admin))
    assert removed.status_code == 200
    assert removed.json()["is_active"] is False
    assert client.get(f"/api/products/{product_id}").status_code == 404
    logs = client.get("/api/admin/audit-logs", headers=auth(admin))
    assert logs.status_code == 200
    assert any(row["action"] == "delete" and row["resource_id"] == product_id for row in logs.json())


@pytest.mark.integration
def test_price_must_be_above_zero(client):
    admin = login(client, "rudraksh@example.com", "rudraksh1234")
    rejected = client.post(
        "/api/admin/products",
        json={
            "sku": "ZERO-1",
            "product_name": "Free Sample",
            "description": "Price is not allowed to be zero",
            "category_id": 1,
            "price": "0",
            "available_quantity": 1,
        },
        headers=auth(admin),
    )
    assert rejected.status_code == 422
