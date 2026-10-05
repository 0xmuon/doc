"""health and metrics over http.these do not need a token."""

import pytest

pytestmark = pytest.mark.integration


def test_health_and_metrics(client):
    live = client.get("/health")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"
    ready = client.get("/health/db")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ok"
    report = client.get("/metrics")
    assert report.status_code == 200
    body = report.json()
    assert "payment_circuit" in body
    assert body["payment_circuit"]["state"] == "closed"
    assert any(path.startswith("GET ") for path in body["routes"])
