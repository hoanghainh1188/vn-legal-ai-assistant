"""VectorRepository — seam tách logic hybrid khỏi tầng dữ liệu Postgres.

`rag.py`/`ingest.py` phụ thuộc protocol này, không biết Postgres cụ thể. Test
tiêm bản giả (fake) → chạy không cần DB thật (FR-008, Constitution III).
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from pgvector import Vector

from app.db.connection import get_pool


# ID tổng hợp ổn định từ khoá tự nhiên, làm khoá tra cứu cho hybrid_rank.
def _synth_id(document_id: str, article_number: int) -> str:
    return f"{document_id}__dieu_{article_number}"


@dataclass(frozen=True)
class ChunkRow:
    """Một chunk pháp lý để ghi vào kho."""

    article_number: int
    article_title: str
    document_id: str
    chapter: str
    content: str


@dataclass(frozen=True)
class RetrievedRow:
    """Một chunk lấy từ kho (kèm embedding để tính relevance, similarity nếu có)."""

    id: str
    article_number: int
    article_title: str
    document_id: str
    chapter: str
    content: str
    embedding: list[float] = field(default_factory=list)
    similarity: float = 0.0


@runtime_checkable
class VectorRepository(Protocol):
    async def upsert_chunks(self, chunks: list[ChunkRow], embeddings: list[list[float]]) -> int: ...

    async def dense_candidates(
        self, query_embedding: list[float], limit: int
    ) -> list[RetrievedRow]: ...

    async def all_rows(self) -> list[RetrievedRow]: ...

    async def count(self) -> int: ...


class PgVectorRepository:
    """Hiện thực VectorRepository trên Postgres + pgvector (psycopg3 async)."""

    async def upsert_chunks(self, chunks: list[ChunkRow], embeddings: list[list[float]]) -> int:
        pool = await get_pool()
        params = [
            (c.document_id, c.article_number, c.article_title, c.chapter, c.content, Vector(e))
            for c, e in zip(chunks, embeddings, strict=True)
        ]
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO legal_chunks
                    (document_id, article_number, article_title, chapter, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id, article_number) DO UPDATE SET
                    article_title = EXCLUDED.article_title,
                    chapter       = EXCLUDED.chapter,
                    content       = EXCLUDED.content,
                    embedding     = EXCLUDED.embedding
                """,
                params,
            )
        return len(chunks)

    async def dense_candidates(
        self, query_embedding: list[float], limit: int
    ) -> list[RetrievedRow]:
        q = Vector(query_embedding)
        pool = await get_pool()
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT document_id, article_number, article_title, chapter, content,
                       embedding, 1 - (embedding <=> %s) AS similarity
                FROM legal_chunks
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (q, q, limit),
            )
            rows = await cur.fetchall()
        return [self._to_row(r, has_similarity=True) for r in rows]

    async def all_rows(self) -> list[RetrievedRow]:
        pool = await get_pool()
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT document_id, article_number, article_title, chapter, content, embedding
                FROM legal_chunks
                """
            )
            rows = await cur.fetchall()
        return [self._to_row(r, has_similarity=False) for r in rows]

    async def count(self) -> int:
        pool = await get_pool()
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute("SELECT count(*) FROM legal_chunks")
            row = await cur.fetchone()
        return int(row[0]) if row else 0

    @staticmethod
    def _to_row(record: tuple, *, has_similarity: bool) -> RetrievedRow:
        document_id, article_number, article_title, chapter, content, embedding = record[:6]
        similarity = float(record[6]) if has_similarity else 0.0
        return RetrievedRow(
            id=_synth_id(document_id, article_number),
            article_number=article_number,
            article_title=article_title,
            document_id=document_id,
            chapter=chapter,
            content=content,
            embedding=[float(x) for x in embedding],
            similarity=similarity,
        )


_repository: VectorRepository | None = None


def get_vector_repository() -> VectorRepository:
    """Factory theo cấu hình. Hiện chỉ có Postgres+pgvector."""
    global _repository
    if _repository is None:
        _repository = PgVectorRepository()
    return _repository
