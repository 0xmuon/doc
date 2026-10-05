"""json lines on the shopping logger.so a request can be found by its id."""

import json
import logging
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.utils import record_request

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def configure_logging() -> None:
    log = logging.getLogger("shopping")
    if log.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False


def log_event(event: str, **fields) -> None:
    payload = {"event": event, "request_id": request_id_var.get(), **fields}
    logging.getLogger("shopping").info(json.dumps(payload))


class RequestLogMiddleware(BaseHTTPMiddleware):
    """one id per request.method and status only,never the token or the body."""

    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            elapsed = round((time.perf_counter() - started) * 1000, 1)
            route = request.scope.get("route")
            template = getattr(route, "path", request.url.path)
            record_request(request.method, template, response.status_code, elapsed)
            log_event(
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                ms=elapsed,
            )
            return response
        except Exception:
            log_event(
                "request_failed",
                method=request.method,
                path=request.url.path,
                ms=round((time.perf_counter() - started) * 1000, 1),
            )
            raise
        finally:
            request_id_var.reset(token)
