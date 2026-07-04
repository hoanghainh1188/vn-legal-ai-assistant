"""Integration tests cho PgVectorRepository — cần Postgres+pgvector thật.

Tự bỏ qua khi thiếu VN_LEGAL_DATABASE_URL để CI/máy dev không có DB vẫn xanh
(logic truy hồi đã được test độc lập DB ở test_vector_store.py).
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("VN_LEGAL_DATABASE_URL"),
    reason="cần VN_LEGAL_DATABASE_URL (Postgres+pgvector) cho test tích hợp",
)


@pytest.mark.integration
class TestPgVectorRepository:
    async def test_upsert_idempotent_and_dense_query(self) -> None:
        from app.db.connection import get_pool
        from app.db.repository import ChunkRow, PgVectorRepository

        repo = PgVectorRepository()
        chunk = ChunkRow(
            article_number=9001,
            article_title="Điều kiểm thử",
            document_id="TEST/2026",
            chapter="I",
            content="Nội dung điều kiểm thử pgvector.",
        )
        emb = [0.01] * 1024

        try:
            await repo.upsert_chunks([chunk], [emb])
            after_first = await repo.count()
            await repo.upsert_chunks([chunk], [emb])  # chạy lại cùng khoá tự nhiên
            assert await repo.count() == after_first  # idempotent, không nhân bản

            dense = await repo.dense_candidates(emb, limit=1)
            assert dense
            assert dense[0].article_number == 9001
        finally:
            # Dọn dữ liệu test để không làm bẩn kho thật.
            pool = await get_pool()
            async with pool.connection() as conn:
                await conn.execute(
                    "DELETE FROM legal_chunks WHERE document_id = %s", (chunk.document_id,)
                )
