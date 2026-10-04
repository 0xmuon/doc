"""stop calling a gateway that keeps failing.a decline is an answer,not an outage."""

import time
from collections.abc import Awaitable, Callable


class CircuitOpenError(Exception):
    """breaker is open.so we fail fast and dont wait on another timeout."""


class CircuitBreaker:
    def __init__(self, name: str, max_failures: int, reset_seconds: float, excluded: tuple[type[BaseException], ...] = ()):
        self.name = name
        self.max_failures = max_failures
        self.reset_seconds = reset_seconds
        self.excluded = excluded
        self.state = "closed"
        self.failures = 0
        self.opened_at = 0.0

    async def call(self, func: Callable[..., Awaitable], *args):
        if self.state == "open":
            if time.monotonic() - self.opened_at < self.reset_seconds:
                raise CircuitOpenError(f"{self.name} circuit breaker is open")
            self.state = "half-open"
        try:
            result = await func(*args)
        except self.excluded:
            self._record_success()
            raise
        except Exception:
            self.failures += 1
            if self.state == "half-open" or self.failures >= self.max_failures:
                self.opened_at = time.monotonic()
                self.state = "open"
            raise
        self._record_success()
        return result

    def _record_success(self) -> None:
        self.failures = 0
        if self.state != "closed":
            self.state = "closed"

    def reset(self) -> None:
        self.state = "closed"
        self.failures = 0
        self.opened_at = 0.0
