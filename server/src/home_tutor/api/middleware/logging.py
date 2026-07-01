"""HTTP request logging middleware."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from home_tutor.core.logging import get_logger, log_trace, reset_request_id, set_request_id

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP requests/responses and propagate request_id via contextvars."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = uuid.uuid4().hex[:8]
        token = set_request_id(request_id)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        log_trace(
            logger,
            "HTTP_REQUEST",
            method=request.method,
            path=request.url.path,
            query=str(request.url.query) or None,
        )
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "HTTP_ERROR",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            structlog.contextvars.clear_contextvars()
            reset_request_id(token)
            raise
        duration_ms = int((time.perf_counter() - start) * 1000)
        log_trace(
            logger,
            "HTTP_RESPONSE",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.clear_contextvars()
        reset_request_id(token)
        return response
