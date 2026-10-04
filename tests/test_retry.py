"""retry stops after the last failure and returns the first success."""

import asyncio

from app.integrations.retry import DeclineError, GatewayError, retry_async


def test_retry_then_success():
    calls = {"n": 0}

    async def once() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise GatewayError("timeout")
        return "ok"

    assert asyncio.run(retry_async(once, attempts=3, base_delay=0, operation="payment")) == "ok"
    assert calls["n"] == 3


def test_retry_gives_up():
    async def once() -> str:
        raise GatewayError("down")

    try:
        asyncio.run(retry_async(once, attempts=2, base_delay=0, operation="payment"))
        raise AssertionError("should have raised")
    except GatewayError as exc:
        assert "down" in str(exc)


def test_decline_is_not_retried():
    calls = {"n": 0}

    async def once() -> str:
        calls["n"] += 1
        raise DeclineError("no")

    try:
        asyncio.run(retry_async(once, attempts=3, base_delay=0, operation="payment"))
        raise AssertionError("should have raised")
    except DeclineError:
        assert calls["n"] == 1
