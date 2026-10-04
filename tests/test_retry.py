"""retry stops after the last failure and returns the first success."""

from app.integrations.retry import GatewayError, call_with_retry


def test_retry_then_success():
    calls = {"n": 0}

    def once(_timeout: float) -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise GatewayError("timeout")
        return "ok"

    assert call_with_retry(once, attempts=3, timeout=0.1, pause=0) == "ok"
    assert calls["n"] == 3


def test_retry_gives_up():
    def once(_timeout: float) -> str:
        raise GatewayError("down")

    try:
        call_with_retry(once, attempts=2, timeout=0.1, pause=0)
        raise AssertionError("should have raised")
    except GatewayError as exc:
        assert "down" in str(exc)
