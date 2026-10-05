"""payment call after the order is already saved.timeouts retry,a decline does not."""

import os
from dataclasses import dataclass

import httpx

from app.integrations import CircuitBreaker, CircuitOpenError, DeclineError, GatewayError, retry_async

PAID = "PAID"
FAILED = "FAILED"

# tests can drop in a MockTransport.left empty in the running app.
http_transport: httpx.AsyncBaseTransport | None = None

payment_breaker = CircuitBreaker(
    "payment",
    max_failures=int(os.getenv("CIRCUIT_MAX_FAILURES", "5")),
    reset_seconds=float(os.getenv("CIRCUIT_RESET_SECONDS", "30")),
    excluded=(DeclineError,),
)


def reset_breaker() -> None:
    payment_breaker.reset()
    payment_breaker.max_failures = int(os.getenv("CIRCUIT_MAX_FAILURES", "5"))
    payment_breaker.reset_seconds = float(os.getenv("CIRCUIT_RESET_SECONDS", "30"))


@dataclass
class PaymentOutcome:
    status: str
    detail: str
    reference: str | None = None


def _settings() -> tuple[int, float, float, str, str]:
    attempts = int(os.getenv("PAYMENT_MAX_ATTEMPTS", "3"))
    timeout = float(os.getenv("PAYMENT_TIMEOUT_SECONDS", "2"))
    delay = float(os.getenv("PAYMENT_RETRY_BASE_DELAY", "0.05"))
    mode = os.getenv("PAYMENT_FORCE", "ok").strip().lower()
    url = os.getenv("PAYMENT_API_URL", "").strip()
    return attempts, timeout, delay, mode, url


async def _local_once() -> tuple[str, str]:
    mode = os.getenv("PAYMENT_FORCE", "ok").strip().lower()
    if mode == "timeout":
        raise GatewayError("Payment gateway timed out")
    if mode == "fail":
        raise DeclineError("Payment gateway declined")
    return PAID, "PAY-LOCAL"


async def _http_once(url: str, body: dict, timeout: float, idempotency_key: str) -> tuple[str, str]:
    headers = {"Idempotency-Key": idempotency_key}
    try:
        async with httpx.AsyncClient(transport=http_transport, timeout=timeout) as client:
            response = await client.post(url, json=body, headers=headers)
    except httpx.TimeoutException as exc:
        raise GatewayError("Payment gateway timed out") from exc
    except httpx.HTTPError as exc:
        raise GatewayError("Payment gateway unreachable") from exc
    if response.status_code == 402:
        raise DeclineError("Payment gateway declined")
    if response.status_code >= 500 or response.status_code == 408:
        raise GatewayError(f"Payment gateway returned {response.status_code}")
    if response.status_code >= 400:
        raise DeclineError(f"Payment gateway returned {response.status_code}")
    payload = response.json()
    status = str(payload.get("status", "")).upper()
    reference = str(payload.get("reference") or "")
    if status != PAID or not reference:
        raise DeclineError("Payment gateway declined")
    return PAID, reference


async def _attempt(order_id: int, amount: str, method: str, order_number: str) -> tuple[str, str]:
    _attempts, timeout, _delay, _mode, url = _settings()
    key = order_number or str(order_id)
    body = {"order_id": order_id, "amount": amount, "payment_method": method, "order_number": order_number}
    if url:
        return await _http_once(url, body, timeout, key)
    return await _local_once()


async def charge_order(order_id: int, amount: str, method: str, order_number: str = "") -> PaymentOutcome:
    """never raises into the route.the order stays,and the status is PAID or FAILED."""
    attempts, _timeout, delay, _mode, _url = _settings()

    async def _with_retry() -> tuple[str, str]:
        return await retry_async(
            _attempt,
            order_id,
            amount,
            method,
            order_number,
            attempts=attempts,
            base_delay=delay,
            operation="payment",
        )

    try:
        _status, reference = await payment_breaker.call(_with_retry)
    except DeclineError as exc:
        return PaymentOutcome(status=FAILED, detail=str(exc))
    except (GatewayError, CircuitOpenError) as exc:
        return PaymentOutcome(status=FAILED, detail=str(exc))
    return PaymentOutcome(status=PAID, detail="Payment accepted", reference=reference)
