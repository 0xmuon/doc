"""retry only the failures that might clear.a decline is a no,and a no is not retried."""

import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger("shopping")


class GatewayError(Exception):
    """timeout,connection error,or 5xx.these can be tried again."""


class DeclineError(GatewayError):
    """the gateway answered no.do not retry and do not open the breaker."""


async def retry_async(func: Callable[..., Awaitable], *args, attempts: int, base_delay: float, operation: str):
    """await func up to attempts times.DeclineError stops the loop on the first no."""
    if attempts < 1:
        raise GatewayError("Payment attempt count must be at least 1")
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await func(*args)
        except DeclineError:
            raise
        except GatewayError as exc:
            last = exc
            if attempt >= attempts:
                logger.warning("%s failed after %d attempts: %s", operation, attempts, exc)
                break
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning("%s failed (attempt %d/%d); retrying in %.2fs", operation, attempt, attempts, delay)
            if delay:
                await asyncio.sleep(delay)
    raise GatewayError(str(last) if last else "External call failed")
