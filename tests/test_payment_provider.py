"""stand-in charges.no database,and slow does not really wait 10 seconds."""

from fastapi.testclient import TestClient

from provider import main as provider_main

client = TestClient(provider_main.app)
CHARGE = {"order_id": 9, "amount": "10.00", "payment_method": "UPI", "order_number": "ORD-000009"}


def setup_function():
    provider_main.mode = "ok"
    provider_main.SLOW_SECONDS = 10
    provider_main.charges.clear()


def test_ok_returns_paid_and_a_reference():
    switched = client.put("/mode/ok")
    assert switched.status_code == 200
    assert switched.json()["mode"] == "ok"
    paid = client.post("/payments/charge", json=CHARGE, headers={"Idempotency-Key": "ORD-000009"})
    assert paid.status_code == 200
    body = paid.json()
    assert body["status"] == "PAID"
    assert body["reference"].startswith("PAY-")
    assert body["order_id"] == 9


def test_fail_returns_503_and_stores_nothing():
    client.put("/mode/fail")
    down = client.post("/payments/charge", json=CHARGE, headers={"Idempotency-Key": "ORD-000009"})
    assert down.status_code == 503
    assert provider_main.charges == {}


def test_slow_waits_then_returns_paid(monkeypatch):
    waited = {"seconds": None}

    async def instant(seconds):
        waited["seconds"] = seconds

    monkeypatch.setattr(provider_main.asyncio, "sleep", instant)
    client.put("/mode/slow")
    paid = client.post("/payments/charge", json=CHARGE, headers={"Idempotency-Key": "ORD-000009"})
    assert paid.status_code == 200
    assert paid.json()["status"] == "PAID"
    assert waited["seconds"] == 10


def test_same_key_is_not_charged_again():
    first = client.post("/payments/charge", json=CHARGE, headers={"Idempotency-Key": "ORD-000009"})
    assert first.status_code == 200
    reference = first.json()["reference"]
    client.put("/mode/fail")
    again = client.post("/payments/charge", json=CHARGE, headers={"Idempotency-Key": "ORD-000009"})
    assert again.status_code == 200
    assert again.json()["reference"] == reference
    assert len(provider_main.charges) == 1


def test_unknown_mode_is_422():
    rejected = client.put("/mode/flaky")
    assert rejected.status_code == 422
