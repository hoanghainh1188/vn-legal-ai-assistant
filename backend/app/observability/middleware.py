"""Request context — pure-ASGI middleware: request-id + timing + structured log.

SSE-safe: chỉ đọc status ở 'http.response.start', chèn header X-Request-ID, và log
1 bản ghi khi request kết thúc. KHÔNG buffer body.
"""

import logging
import re
import time
from uuid import uuid4

from opentelemetry import trace
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.observability.logging_config import request_id_var

logger = logging.getLogger("app.request")

# Chỉ tin X-Request-ID của client nếu đúng định dạng an toàn (tránh log bloat / reflection).
_REQUEST_ID_RE = re.compile(r"^[0-9A-Za-z._-]{8,64}$")


def _resolve_request_id(headers: Headers) -> str:
    candidate = headers.get("x-request-id", "")
    return candidate if _REQUEST_ID_RE.match(candidate) else uuid4().hex


def _current_trace_id() -> str | None:
    ctx = trace.get_current_span().get_span_context()
    return format(ctx.trace_id, "032x") if ctx.is_valid else None


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _resolve_request_id(Headers(scope=scope))
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message).setdefault("X-Request-ID", request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            # KHÔNG log query string/body (tránh PII) — chỉ metadata request.
            logger.info(
                "request",
                extra={
                    "request_id": request_id,
                    "trace_id": _current_trace_id(),  # tương quan log ↔ trace (FR-014)
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            request_id_var.reset(token)
