"""Áp schema kho vector vào Postgres+pgvector (idempotent).

uv run python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.connection import require_database_url

SCHEMA_FILE = Path(__file__).resolve().parent.parent / "app" / "db" / "schema.sql"


async def apply_schema() -> None:
    """Chạy từng câu lệnh trong schema.sql (idempotent, CREATE ... IF NOT EXISTS).

    Dùng kết nối THUẦN (không đăng ký kiểu pgvector) vì chính bước này tạo
    `EXTENSION vector` — pool thường (có register_vector) chỉ dùng được sau đó.
    """
    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    async with await psycopg.AsyncConnection.connect(
        require_database_url(), autocommit=True
    ) as conn:
        for stmt in statements:
            await conn.execute(stmt)


async def main() -> None:
    await apply_schema()
    print(f"Schema đã áp từ {SCHEMA_FILE.name} (idempotent).")


if __name__ == "__main__":
    asyncio.run(main())
