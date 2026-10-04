"""http checks for the token pair.the app and sqlite file come from conftest."""

from tests.helpers import auth, login, register


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


def test_access_token_is_rejected_on_refresh(client):
    register(client, "access-on-refresh@example.com")
    access = login(client, "access-on-refresh@example.com")
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": access})
    assert refreshed.status_code == 401
