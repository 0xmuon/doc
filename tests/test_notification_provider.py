"""fake notification provider.no database,and slow does not really wait 10 seconds."""

from fastapi.testclient import TestClient

from provider import main as provider_main

client = TestClient(provider_main.app)
NOTICE = {"order_id": 3, "email": "buyer@example.com", "payment_status": "PAID"}


def setup_function():
    provider_main.mode = "ok"
    provider_main.SLOW_SECONDS = 10


def test_ok_returns_200_at_once():
    switched = client.put("/mode/ok")
    assert switched.status_code == 200
    assert switched.json()["mode"] == "ok"
    sent = client.post("/notify", json=NOTICE)
    assert sent.status_code == 200
    assert sent.json()["status"] == "sent"


def test_fail_returns_503_at_once():
    client.put("/mode/fail")
    sent = client.post("/notify", json=NOTICE)
    assert sent.status_code == 503


def test_slow_waits_then_returns_200(monkeypatch):
    waited = {"seconds": None}

    async def instant(seconds):
        waited["seconds"] = seconds

    monkeypatch.setattr(provider_main.asyncio, "sleep", instant)
    client.put("/mode/slow")
    sent = client.post("/notify", json=NOTICE)
    assert sent.status_code == 200
    assert waited["seconds"] == 10


def test_unknown_mode_is_422():
    rejected = client.put("/mode/flaky")
    assert rejected.status_code == 422


def test_docs_only_list_the_mode_routes():
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {"/mode", "/mode/{next_mode}"}
    assert set(paths["/mode"]) == {"get"}
    assert set(paths["/mode/{next_mode}"]) == {"put"}
