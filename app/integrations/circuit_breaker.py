"""stop calling a gateway that keeps failing.a decline is an answer,not an outage.

three gateway failures move the breaker to half-open.
the next failure turns it fully off.
it stays off until the fake payment API is ok again.
"""

from collections.abc import Awaitable, Callable


class CircuitOpenError(Exception):
    """breaker is off.so we fail fast and dont wait on another timeout."""


def _log(event: str, **fields) -> None:
    from app.utils.logging_setup import log_event

    log_event(event, **fields)


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        max_failures: int = 3,
        reset_seconds: float = 30,
        excluded: tuple[type[BaseException], ...] = (),
        provider_is_up: Callable[[], Awaitable[bool]] | None = None,
    ):
        self.name = name
        self.max_failures = max_failures
        self.reset_seconds = reset_seconds
        self.excluded = excluded
        self.provider_is_up = provider_is_up
        self.state = "closed"
        self.failures = 0
        self.opened_at = 0.0

    async def call(self, func: Callable[..., Awaitable], *args):
        if self.state == "open":
            up = False
            if self.provider_is_up is not None:
                up = await self.provider_is_up()
            if not up:
                _log(
                    "circuit_off",
                    name=self.name,
                    state="open",
                    transition="open -> open",
                    detail="payment api is still down, charge skipped",
                )
                raise CircuitOpenError(f"{self.name} circuit breaker is off")
            self._set_state("half-open", "fake payment api is back on, trying one charge")
        try:
            result = await func(*args)
        except self.excluded:
            raise
        except Exception:
            self.failures += 1
            if self.state == "half-open":
                self._set_state("open", "half-open charge failed, breaker is off")
            elif self.failures >= self.max_failures:
                self._set_state("half-open", f"{self.failures} payment failures, breaker is half-open")
            else:
                _log(
                    "circuit_failure",
                    name=self.name,
                    state=self.state,
                    transition=f"{self.state} -> {self.state}",
                    failures=self.failures,
                    max_failures=self.max_failures,
                    detail=f"payment failure {self.failures} of {self.max_failures}, still closed",
                )
            raise
        if self.state != "closed":
            self._set_state("closed", "payment succeeded")
        self.failures = 0
        return result

    def _set_state(self, state: str, detail: str) -> None:
        previous = self.state
        self.state = state
        _log(
            "circuit_state",
            name=self.name,
            previous=previous,
            state=state,
            transition=f"{previous} -> {state}",
            failures=self.failures,
            detail=detail,
        )

    def reset(self) -> None:
        self.state = "closed"
        self.failures = 0
        self.opened_at = 0.0
