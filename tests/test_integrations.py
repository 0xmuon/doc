"""gateway client.fakes stand in for the network.no database."""

import asyncio

import httpx
import pytest

from app.integrations import payment_gateway
from app.integrations.circuit_breaker import CircuitBreaker, CircuitOpenError
from app.integrations.payment_gateway import charge_order, reset_breaker
from app.integrations.retry import DeclineError, GatewayError
from tests.fakes import json_response, scripted_transport


def test_breaker_opens_and_fails_fast():
    breaker = CircuitBreaker("payment", max_failures=2, reset_seconds=60)

    async def down():
        raise GatewayError("timeout")

    async def run():
        with pytest.raises(GatewayError):
            await breaker.call(down)
        with pytest.raises(GatewayError):
            await breaker.call(down)
        assert breaker.state == "open"
        with pytest.raises(CircuitOpenError):
            await breaker.call(down)

    asyncio.run(run())


def test_decline_does_not_open_the_breaker():
    breaker = CircuitBreaker("payment", max_failures=1, reset_seconds=60, excluded=(DeclineError,))

    async def decline():
        raise DeclineError("no")

    async def run():
        with pytest.raises(DeclineError):
            await breaker.call(decline)
        assert breaker.state == "closed"

    asyncio.run(run())


def test_http_decline_is_not_retried(monkeypatch):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert request.headers["Idempotency-Key"] == "9"
        return json_response(402, {"status": "FAILED"})

    monkeypatch.setenv("PAYMENT_API_URL", "http://gateway.test/charge")
    monkeypatch.setenv("PAYMENT_MAX_ATTEMPTS", "3")
    payment_gateway.http_transport = scripted_transport(handler)
    reset_breaker()
    try:
        outcome = asyncio.run(charge_order(9, "10.00", "UPI"))
    finally:
        payment_gateway.http_transport = None
        reset_breaker()
    assert outcome.status == "FAILED"
    assert calls["n"] == 1


def test_http_5xx_is_retried_then_paid(monkeypatch):
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return json_response(503, {"status": "FAILED"})
        return json_response(200, {"status": "PAID"})

    monkeypatch.setenv("PAYMENT_API_URL", "http://gateway.test/charge")
    monkeypatch.setenv("PAYMENT_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("PAYMENT_RETRY_BASE_DELAY", "0")
    payment_gateway.http_transport = scripted_transport(handler)
    reset_breaker()
    try:
        outcome = asyncio.run(charge_order(4, "10.00", "CARD"))
    finally:
        payment_gateway.http_transport = None
        reset_breaker()
    assert outcome.status == "PAID"
    assert calls["n"] == 3
