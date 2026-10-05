"""shopping api calls the real notification provider over http.skipped when that process is down."""

import os

import httpx
import pytest

from tests.helpers import auth, login, register

pytestmark = pytest.mark.integration


def _provider_base() -> str | None:
    candidates = [os.getenv("NOTIFY_PROVIDER_URL", "").strip(), "http://provider:9000", "http://127.0.0.1:9000"]
    for base in candidates:
        if not base:
            continue
        try:
            response = httpx.get(f"{base}/mode", timeout=1.0)
        except httpx.HTTPError:
            continue
        if response.status_code == 200:
            return base.rstrip("/")
    return None


def test_notice_is_delivered_to_the_provider(client, monkeypatch):
    base = _provider_base()
    if base is None:
        pytest.skip("fake notification provider is not running")
    httpx.put(f"{base}/mode/ok", timeout=2.0)
    httpx.delete(f"{base}/sent", timeout=2.0)
    monkeypatch.setenv("NOTIFY_API_URL", f"{base}/notify")

    register(client, "notice-buyer@example.com")
    token = login(client, "notice-buyer@example.com")
    user_id = client.post(
        "/api/auth/login",
        json={"email": "notice-buyer@example.com", "password": "secret123"},
    ).json()["user"]["user_id"]
    added = client.post(
        "/api/cart/add",
        json={"user_id": user_id, "product_id": 3, "quantity": 1},
        headers=auth(token),
    )
    assert added.status_code == 201, added.text
    checked = client.post(
        "/api/orders/checkout",
        json={"user_id": user_id, "payment_method": "UPI"},
        headers=auth(token),
    )
    assert checked.status_code == 201, checked.text
    order_id = checked.json()["order"]["order_id"]

    sent = httpx.get(f"{base}/sent", timeout=2.0).json()
    assert any(row["order_id"] == order_id and row["email"] == "notice-buyer@example.com" for row in sent)
