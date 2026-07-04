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
    # Metadata hiệu lực cấp văn bản (Feature #7); None nếu chưa biết.
    document_name: str | None = None
    eff_status: str | None = None
    eff_date: str | None = None
    domain: str | None = None  # lĩnh vực (Feature #8)


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
    document_name: str | None = None
    eff_status: str | None = None
    eff_date: str | None = None
    domain: str | None = None


@runtime_checkable
class VectorRepository(Protocol):
    async def upsert_chunks(self, chunks: list[ChunkRow], embeddings: list[list[float]]) -> int: ...

    async def dense_candidates(
        self, query_embedding: list[float], limit: int, domain: str | None = None
    ) -> list[RetrievedRow]: ...

    async def all_rows(self, domain: str | None = None) -> list[RetrievedRow]: ...

    async def list_domains(self) -> list[str]: ...

    async def count(self) -> int: ...


class PgVectorRepository:
    """Hiện thực VectorRepository trên Postgres + pgvector (psycopg3 async)."""

    async def upsert_chunks(self, chunks: list[ChunkRow], embeddings: list[list[float]]) -> int:
        pool = await get_pool()
        params = [
            (
                c.document_id,
                c.article_number,
                c.article_title,
                c.chapter,
                c.content,
                c.document_name,
                c.eff_status,
                c.eff_date,
                c.domain,
                Vector(e),
            )
            for c, e in zip(chunks, embeddings, strict=True)
        ]
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO legal_chunks
                    (document_id, article_number, article_title, chapter, content,
                     document_name, eff_status, eff_date, domain, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id, article_number) DO UPDATE SET
                    article_title = EXCLUDED.article_title,
                    chapter       = EXCLUDED.chapter,
                    content       = EXCLUDED.content,
                    domain        = EXCLUDED.domain,
                    document_name = EXCLUDED.document_name,
                    eff_status    = EXCLUDED.eff_status,
                    eff_date      = EXCLUDED.eff_date,
                    embedding     = EXCLUDED.embedding
                """,
                params,
            )
        return len(chunks)

    async def dense_candidates(
        self, query_embedding: list[float], limit: int, domain: str | None = None
    ) -> list[RetrievedRow]:
        q = Vector(query_embedding)
        where = "WHERE domain = %s" if domain else ""
        # Thứ tự %s: similarity(q) → [domain] → ORDER BY(q) → LIMIT.
        params: list = [q, *([domain] if domain else []), q, limit]
        pool = await get_pool()
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT document_id, article_number, article_title, chapter, content,
                       document_name, eff_status, eff_date, domain,
                       embedding, 1 - (embedding <=> %s) AS similarity
                FROM legal_chunks
                {where}
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                params,
            )
            rows = await cur.fetchall()
        return [self._to_row(r, has_similarity=True) for r in rows]

    async def all_rows(self, domain: str | None = None) -> list[RetrievedRow]:
        where = "WHERE domain = %s" if domain else ""
        params: list = [domain] if domain else []
        pool = await get_pool()
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT document_id, article_number, article_title, chapter, content,
                       document_name, eff_status, eff_date, domain, embedding
                FROM legal_chunks
                {where}
                """,
                params,
            )
            rows = await cur.fetchall()
        return [self._to_row(r, has_similarity=False) for r in rows]

    async def list_domains(self) -> list[str]:
        pool = await get_pool()
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT DISTINCT domain FROM legal_chunks WHERE domain IS NOT NULL ORDER BY domain"
            )
            rows = await cur.fetchall()
        return [r[0] for r in rows]

    async def count(self) -> int:
        pool = await get_pool()
        async with pool.connection() as conn, conn.cursor() as cur:
            await cur.execute("SELECT count(*) FROM legal_chunks")
            row = await cur.fetchone()
        return int(row[0]) if row else 0

    @staticmethod
    def _to_row(record: tuple, *, has_similarity: bool) -> RetrievedRow:
        (
            document_id,
            article_number,
            article_title,
            chapter,
            content,
            document_name,
            eff_status,
            eff_date,
            domain,
            embedding,
        ) = record[:10]
        similarity = float(record[10]) if has_similarity else 0.0
        return RetrievedRow(
            id=_synth_id(document_id, article_number),
            article_number=article_number,
            article_title=article_title,
            document_id=document_id,
            chapter=chapter,
            content=content,
            embedding=[float(x) for x in embedding],
            similarity=similarity,
            document_name=document_name,
            eff_status=eff_status,
            eff_date=eff_date.isoformat() if eff_date is not None else None,
            domain=domain,
        )


_repository: VectorRepository | None = None


def get_vector_repository() -> VectorRepository:
    """Factory theo cấu hình. Hiện chỉ có Postgres+pgvector."""
    global _repository
    if _repository is None:
        _repository = PgVectorRepository()
    return _repository
