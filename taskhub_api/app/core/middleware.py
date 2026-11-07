import logging
import re
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("taskhub.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming_id = request.headers.get("X-Request-ID", "")
        valid_incoming = bool(re.fullmatch(r"[A-Za-z0-9._-]{1,100}", incoming_id))
        request_id = incoming_id if valid_incoming else uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            if "response" in locals():
                response.headers["X-Process-Time-ms"] = str(elapsed_ms)
            logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                status_code,
                elapsed_ms,
            )
