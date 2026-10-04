"""payment call with a timeout and a few retries.order row is already saved before this runs."""

import os
from dataclasses import dataclass

import httpx

from app.integrations.retry import GatewayError, call_with_retry

PAID = "PAID"
FAILED = "FAILED"


@dataclass
class PaymentOutcome:
    status: str
    detail: str


def _settings() -> tuple[int, float, str]:
    attempts = int(os.getenv("PAYMENT_MAX_ATTEMPTS", "3"))
    timeout = float(os.getenv("PAYMENT_TIMEOUT_SECONDS", "2"))
    mode = os.getenv("PAYMENT_FORCE", "ok").strip().lower()
    return attempts, timeout, mode


def _local_once(timeout: float) -> str:
    """stand-in gateway.PAYMENT_FORCE=fail or timeout shows the retry path without a network."""
    _, _, mode = _settings()
    if mode == "timeout":
        raise GatewayError(f"Payment gateway timed out after {timeout}s")
    if mode == "fail":
        raise GatewayError("Payment gateway declined")
    return PAID


def _http_once(url: str, body: dict, timeout: float) -> str:
    try:
        response = httpx.post(url, json=body, timeout=timeout)
    except httpx.TimeoutException as exc:
        raise GatewayError("Payment gateway timed out") from exc
    except httpx.HTTPError as exc:
        raise GatewayError("Payment gateway unreachable") from exc
    if response.status_code >= 400:
        raise GatewayError(f"Payment gateway returned {response.status_code}")
    payload = response.json()
    status = str(payload.get("status", "")).upper()
    if status != PAID:
        raise GatewayError("Payment gateway declined")
    return PAID


def charge_order(order_id: int, amount: str, method: str) -> PaymentOutcome:
    """never raises for a decline.caller stores PAID or FAILED and the order stays."""
    attempts, timeout, _mode = _settings()
    url = os.getenv("PAYMENT_API_URL", "").strip()
    body = {"order_id": order_id, "amount": amount, "payment_method": method}

    def once(limit: float) -> str:
        if url:
            return _http_once(url, body, limit)
        return _local_once(limit)

    try:
        call_with_retry(once, attempts=attempts, timeout=timeout)
    except GatewayError as exc:
        return PaymentOutcome(status=FAILED, detail=str(exc))
    return PaymentOutcome(status=PAID, detail="Payment accepted")
