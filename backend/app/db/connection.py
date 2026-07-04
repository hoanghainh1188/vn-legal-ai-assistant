"""Kết nối Postgres async (psycopg3) + đăng ký kiểu pgvector.

Fail-fast khi thiếu cấu hình DB. KHÔNG log chuỗi kết nối (chứa mật khẩu) —
chỉ log host (Constitution V, FR-006/FR-007).
"""

import logging
from urllib.parse import urlsplit

from pgvector.psycopg import register_vector_async
from psycopg_pool import AsyncConnectionPool

from app.config import settings

logger = logging.getLogger(__name__)

_pool: AsyncConnectionPool | None = None


def require_database_url() -> str:
    url = settings.database_url
    if not url:
        raise RuntimeError(
            "Thiếu cấu hình cơ sở dữ liệu: hãy đặt biến môi trường VN_LEGAL_DATABASE_URL "
            "(vd postgresql://user:pass@host:5432/vn_legal)."
        )
    return url


async def _configure(conn) -> None:
    # Đăng ký adapter vector cho mỗi kết nối trong pool.
    await register_vector_async(conn)


async def get_pool() -> AsyncConnectionPool:
    """Trả pool async (khởi tạo lười, mở một lần)."""
    global _pool
    if _pool is None:
        url = require_database_url()
        pool = AsyncConnectionPool(
            url,
            open=False,
            min_size=1,
            max_size=5,
            configure=_configure,
        )
        await pool.open()
        _pool = pool
        # Chỉ log host, KHÔNG log toàn bộ connection string (có mật khẩu).
        logger.info("Kết nối Postgres host=%s", urlsplit(url).hostname or "?")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
