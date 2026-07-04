# Contract: VectorRepository

**Feature**: `003-postgres-pgvector` | **Date**: 2026-07-04

Seam tách logic hybrid khỏi tầng dữ liệu. `rag.py`/`ingest.py` phụ thuộc **protocol** này, không
biết Postgres. Test tiêm `FakeVectorRepository`.

## Protocol (`app/db/repository.py`)

```python
@runtime_checkable
class VectorRepository(Protocol):
    async def upsert_chunks(
        self, chunks: list[ChunkRow], embeddings: list[list[float]]
    ) -> int:
        """Ghi/cập nhật idempotent theo (document_id, article_number). Trả số bản ghi."""
        ...

    async def dense_candidates(
        self, query_embedding: list[float], limit: int
    ) -> list[RetrievedRow]:
        """Top-`limit` theo cosine `<=>` (kèm distance/similarity)."""
        ...

    async def all_rows(self) -> list[RetrievedRow]:
        """Toàn bộ rows (cho lexical BM25-lite Python). Nhỏ (293)."""
        ...

    async def count(self) -> int:
        ...
```

- `ChunkRow`: `article_number, article_title, document_id, chapter, content`.
- `RetrievedRow`: `ChunkRow` + `similarity: float` (dense; với `all_rows` để 0.0/None).

## Hàm thuần hybrid (`app/services/vector_store.py`)

Giữ nguyên chữ ký/logic, **đổi nguồn dữ liệu từ Chroma sang rows**:

```python
def hybrid_rank(
    query_embedding: list[float],   # để tính relevance_score = cosine(query, row.embedding)
    query_text: str,
    dense: list[RetrievedRow],      # từ repo.dense_candidates (đã sắp theo cosine)
    corpus: list[RetrievedRow],     # từ repo.all_rows (cho IDF/lexical + tra cứu theo id)
    top_k: int = 8,
    rrf_k: int = 60,
) -> list[SourceDocument]: ...
```

- Bảo toàn: IDF `log(1 + (N - df + 0.5)/(df + 0.5))`, title ×3, RRF `1/(rrf_k + rank)`, guarantee
  `top_k // 2 - 1` slot cho khớp tiêu đề mạnh, khử trùng.
- **Thuần** (không I/O) → test trực tiếp, không cần DB.

## Điều phối (`app/services/rag.py`)

```python
repo = get_vector_repository()                       # factory theo config
q_emb = await get_embedding_provider().embed_text(query)
dense = await repo.dense_candidates(q_emb, settings.vector_pool)   # ~30
corpus = await repo.all_rows()
sources = hybrid_rank(q_emb, query, dense, corpus, top_k=settings.retrieval_top_k)
# ... phần prompt + stream LLM giữ nguyên
```

## Hành vi lỗi
- Thiếu/không hợp lệ `DATABASE_URL` → khởi tạo pool raise lỗi rõ ràng (FR-007); KHÔNG log secret.
- Bảng rỗng → `dense_candidates`/`all_rows` trả `[]`; `hybrid_rank([], [], ...)` trả `[]` an toàn.
- Ghi vector ≠ 1024 chiều → lỗi từ Postgres/pgvector, bề mặt lên rõ ràng.

## Bản giả cho test (`FakeVectorRepository`)
- Giữ list `RetrievedRow` trong bộ nhớ; `dense_candidates` sắp theo similarity đặt sẵn (mô phỏng
  Điều 58 dense rank thấp), `all_rows` trả toàn bộ → test guarantee/hybrid chạy không cần Postgres.
