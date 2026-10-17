"""order notice.after checkout or pay-again this runs in the background so the response is not waiting on it."""

import os

import httpx

from app.integrations import DeclineError, GatewayError, retry_async


def _log(event: str, **fields) -> None:
    from app.utils.logging_setup import log_event

    # kind is always "notification" so `docker compose logs api` can be grepped for it.
    log_event(event, kind="notification", **fields)


async def send_order_notification(
    order_id: int,
    email: str,
    payment_status: str,
    trigger: str = "checkout",
) -> None:
    """log always.http only if NOTIFY_API_URL is set.a failed notice does not undo the order.

    trigger is checkout after place-order, payment_retry after pay-again, or manual from /notifications/send.
    """
    _log(
        "notification_started",
        order_id=order_id,
        email=email,
        payment_status=payment_status,
        trigger=trigger,
        detail="payment notification queued",
    )
    url = os.getenv("NOTIFY_API_URL", "").strip()
    if not url:
        _log(
            "notification_skipped",
            order_id=order_id,
            email=email,
            payment_status=payment_status,
            trigger=trigger,
            detail="NOTIFY_API_URL is empty",
        )
        return
    body = {"order_id": order_id, "email": email, "payment_status": payment_status}
    timeout = float(os.getenv("PAYMENT_TIMEOUT_SECONDS", "2"))

    async def once() -> str:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=body)
        except httpx.TimeoutException as exc:
            raise GatewayError("Notification timed out") from exc
        except httpx.HTTPError as exc:
            raise GatewayError("Notification unreachable") from exc
        if response.status_code >= 500:
            raise GatewayError(f"Notification returned {response.status_code}")
        if response.status_code >= 400:
            raise DeclineError(f"Notification returned {response.status_code}")
        return "sent"

    try:
        await retry_async(
            once,
            attempts=int(os.getenv("NOTIFY_MAX_ATTEMPTS", "3")),
            base_delay=float(os.getenv("PAYMENT_RETRY_BASE_DELAY", "0.05")),
            operation="notification",
        )
        _log(
            "notification_sent",
            order_id=order_id,
            email=email,
            payment_status=payment_status,
            trigger=trigger,
            detail="payment notification delivered",
        )
    except (GatewayError, DeclineError) as exc:
        _log(
            "notification_failed",
            order_id=order_id,
            email=email,
            payment_status=payment_status,
            trigger=trigger,
            detail=str(exc),
        )
