"""http checks for the token pair.the app and postgres database come from conftest."""

import pytest

from tests.helpers import auth, login, register

pytestmark = pytest.mark.integration


def test_refresh_issues_a_new_access_token(client):
    register(client, "refresh-user@example.com")
    body = client.post(
        "/api/auth/login",
        json={"email": "refresh-user@example.com", "password": "secret123"},
    ).json()
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert refreshed.status_code == 200, refreshed.text
    access = refreshed.json()["access_token"]
    me = client.get("/api/orders/me", headers=auth(access))
    assert me.status_code == 200


def test_refresh_token_is_rejected_as_a_bearer(client):
    register(client, "refresh-bearer@example.com")
    token = login(client, "refresh-bearer@example.com")
    body = client.post(
        "/api/auth/login",
        json={"email": "refresh-bearer@example.com", "password": "secret123"},
    ).json()
    blocked = client.get("/api/orders/me", headers=auth(body["refresh_token"]))
    assert blocked.status_code == 401
    assert token


def test_swagger_login_uses_email_as_username(client):
    logged = client.post(
        "/api/auth/token",
        data={"username": "rudraksh@example.com", "password": "rudraksh1234"},
    )
    assert logged.status_code == 200, logged.text
    body = logged.json()
    assert body["user"]["role"] == "ADMIN"
    me = client.get("/api/orders/me", headers=auth(body["access_token"]))
    assert me.status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/api/auth/token" not in schema["paths"]
    schemes = schema["components"]["securitySchemes"]
    assert "description" not in schemes["Login"]
    assert "description" not in schemes["JWT"]
    cart = schema["paths"]["/api/cart/{user_id}"]["get"]["security"]
    assert {"JWT": []} in cart
    assert {"Login": []} in cart
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert ".scope-def{display:none}" in docs.text


def test_access_token_is_rejected_on_refresh(client):
    register(client, "access-on-refresh@example.com")
    access = login(client, "access-on-refresh@example.com")
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": access})
    assert refreshed.status_code == 401
