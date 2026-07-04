# Research (Phase 0): Postgres + pgvector migration

**Feature**: `003-postgres-pgvector` | **Date**: 2026-07-04

Giải quyết các ẩn số kỹ thuật trước khi thiết kế. Quyết định đã chốt ở `speckit-clarify`
(xem `docs/04-decisions/2026-07-04-feature-003-postgres-pgvector.md`).

## R1 — Driver Postgres: psycopg3 (async)
- **Quyết định**: `psycopg` v3 async + pool, đăng ký kiểu vector qua gói `pgvector`
  (`pgvector.psycopg.register_vector_async`).
- **Lý do**: async khớp FastAPI/luồng RAG; API sạch; `pgvector` có adapter chính thức cho psycopg3.
  Không ORM (Constitution VI).
- **Thay thế bị loại**: SQLAlchemy (thừa cho Pha 1); asyncpg (adapter pgvector kém tiện hơn psycopg3).

## R2 — Kiểu & index vector
- **Quyết định**: cột `embedding vector(1024)`; index **HNSW** với `vector_cosine_ops`; truy vấn
  bằng toán tử cosine `<=>`, sắp x:  `ORDER BY embedding <=> $query LIMIT n`.
- **Lý do**: bge-m3 = 1024 chiều; PoC dùng cosine (Chroma `hnsw:space=cosine`). HNSW cho recall tốt,
  là mặc định khuyến nghị của pgvector cho truy vấn ANN.
- **Ghi chú**: similarity = `1 - (embedding <=> query)`; chỉ dùng để xếp hạng, logic hybrid ở Python.

## R3 — Giữ nguyên hybrid retrieval
- **Quyết định**: `query_hybrid` cũ tách làm 2 phần: (a) **truy cập dữ liệu** (repository: lấy top
  dense theo `<=>`, và lấy toàn bộ rows cho lexical) + (b) **logic thuần** (IDF/BM25-lite title×3,
  RRF `rrf_k=60`, guarantee-slot) giữ **nguyên xi** trong `vector_store.py`, thao tác trên list rows.
- **Lý do**: bảo toàn hành vi (Constitution I) + test được không cần DB (Constitution III, FR-008).
- **Tương đương Chroma**: `collection.query(n_results=vector_pool)` → `SELECT ... ORDER BY <=> LIMIT`;
  `collection.get()` (toàn bộ) → `SELECT ...` không LIMIT (293 rows).

## R4 — Ingest idempotent
- **Quyết định**: `INSERT ... ON CONFLICT (document_id, article_number) DO UPDATE`; hoặc `TRUNCATE`
  rồi bulk-insert. Khóa tự nhiên = `(document_id, article_number)`.
- **Lý do**: chạy lại ingest không nhân bản (FR-005). Bulk qua `executemany`/`COPY`.

## R5 — Schema/migration
- **Quyết định**: `app/db/schema.sql` (idempotent: `CREATE EXTENSION IF NOT EXISTS vector`,
  `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`) + runner `scripts/init_db.py`.
- **Lý do**: đơn giản, minh bạch, không thêm phụ thuộc (D4). Alembic để Pha 6 nếu cần.

## R6 — DB dev local & test
- **Quyết định**: `docker-compose.yml` thêm service `db: pgvector/pgvector:pg16`. Unit test dùng
  `FakeVectorRepository` (in-memory rows). Test kết nối thật (`test_repository`) gắn nhãn/`skip` khi
  không có `DATABASE_URL` để CI nhẹ vẫn xanh.
- **Lý do**: test-first nhanh (Constitution III); pgvector cùng engine Supabase (D5) nên không phải
  làm lại ở Pha 6.

## R7 — Cấu hình & bảo mật
- **Quyết định**: `settings.database_url` (env `VN_LEGAL_DATABASE_URL`). Thiếu/không hợp lệ → raise
  lỗi rõ ràng khi khởi tạo pool. KHÔNG log connection string (có mật khẩu).
- **Lý do**: FR-006/FR-007, Constitution V.
