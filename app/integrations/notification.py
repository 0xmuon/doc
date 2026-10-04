"""order notice.after checkout this runs in the background so the response is not waiting on it."""

import json
import logging
import os

import httpx

from app.integrations.retry import GatewayError, call_with_retry

logger = logging.getLogger("shopping")


def _log(event: str, **fields) -> None:
    logger.info(json.dumps({"event": event, **fields}))


def send_order_notification(order_id: int, email: str, payment_status: str) -> None:
    """log always.http only if NOTIFY_API_URL is set.a failed notice does not undo the order."""
    _log("order_notification", order_id=order_id, email=email, payment_status=payment_status)
    url = os.getenv("NOTIFY_API_URL", "").strip()
    if not url:
        return
    body = {"order_id": order_id, "email": email, "payment_status": payment_status}

    def once(timeout: float) -> str:
        try:
            response = httpx.post(url, json=body, timeout=timeout)
        except httpx.TimeoutException as exc:
            raise GatewayError("Notification timed out") from exc
        except httpx.HTTPError as exc:
            raise GatewayError("Notification unreachable") from exc
        if response.status_code >= 400:
            raise GatewayError(f"Notification returned {response.status_code}")
        return "sent"

    try:
        call_with_retry(once, attempts=int(os.getenv("NOTIFY_MAX_ATTEMPTS", "3")), timeout=2.0)
        _log("order_notification_sent", order_id=order_id)
    except GatewayError as exc:
        _log("order_notification_failed", order_id=order_id, detail=str(exc))
