"""Rate-limit endpoint công khai bằng slowapi (in-memory, theo IP).

Ngưỡng đọc từ `settings.rate_limit` qua callable → cấu hình runtime + test override
được. Redis đa-instance để Pha 6.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

limiter = Limiter(key_func=get_remote_address)


def rate_limit_value(*_args: object) -> str:
    """Ngưỡng hiện tại (vd '30/minute'). Đọc mỗi request để cấu hình được.

    `*_args` để tương thích cách slowapi gọi callable (có/không truyền `request`
    tùy version).
    """
    return settings.rate_limit


def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """Trả 429 rõ ràng, KHÔNG lộ chi tiết nội bộ; kèm Retry-After nếu có (RFC 6585)."""
    headers: dict[str, str] = {}
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return JSONResponse(
        status_code=429,
        headers=headers or None,
        content={"error": "Bạn thao tác quá nhanh. Vui lòng thử lại sau giây lát."},
    )
