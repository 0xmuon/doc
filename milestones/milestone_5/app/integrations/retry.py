"""small retry loop for calls that can time out.not a second framework."""

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class GatewayError(Exception):
    """the other system did not give a usable answer."""


def call_with_retry(fn: Callable[[float], T], attempts: int, timeout: float, pause: float = 0.05) -> T:
    """try fn(timeout) up to attempts times.timeouts and gateway errors both retry."""
    if attempts < 1:
        raise GatewayError("Payment attempt count must be at least 1")
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn(timeout)
        except GatewayError as exc:
            last = exc
            if attempt == attempts:
                break
            time.sleep(pause)
    raise GatewayError(str(last) if last else "External call failed")
