# Tasks: Migrate kho vector sang Postgres + pgvector

**Feature**: `003-postgres-pgvector` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Tests**: BẮT BUỘC (Constitution — Principle III: test-first). Test viết trước implementation.

**Format**: `- [ ] [TaskID] [P?] [Story?] Mô tả + đường dẫn file`

---

## Phase 1: Setup

- [ ] T001 Sửa `backend/pyproject.toml`: thêm `psycopg[binary]>=3.2`, `pgvector>=0.3`; **gỡ** `chromadb`
- [ ] T002 Chạy `uv sync` trong `backend/`
- [ ] T003 [P] Thêm config vào `backend/app/config.py`: `database_url` (env `VN_LEGAL_DATABASE_URL`), `vector_pool` (default 30); giữ `retrieval_top_k`; **gỡ** `chroma_persist_dir`, `collection_name`
- [ ] T004 [P] Sửa `docker-compose.yml`: thêm service `db` (`pgvector/pgvector:pg16`, volume `pg_data`, port 5432); gỡ volume `chroma_data`; backend nhận `VN_LEGAL_DATABASE_URL`

## Phase 2: Foundational (chặn tất cả user story)

- [ ] T005 Tạo `backend/app/db/__init__.py`
- [ ] T006 Tạo `backend/app/db/schema.sql` theo [data-model.md](./data-model.md): `CREATE EXTENSION IF NOT EXISTS vector`, bảng `legal_chunks` (UNIQUE `(document_id, article_number)`), index HNSW `vector_cosine_ops` — idempotent
- [ ] T007 Định nghĩa `VectorRepository` (Protocol) + `ChunkRow`, `RetrievedRow` trong `backend/app/db/repository.py` theo [contracts/vector-repository.md](./contracts/vector-repository.md)
- [ ] T008 Hiện thực `connection.py` trong `backend/app/db/`: async pool psycopg3 + `register_vector_async`; **fail-fast** khi thiếu/không hợp lệ `database_url`; KHÔNG log connection string

---

## Phase 3: User Story 1 — Giữ nguyên hành vi truy hồi (P1) 🎯 MVP

**Goal**: Chuyển truy hồi sang pgvector nhưng logic hybrid + kết quả **không đổi**. **Independent test**: `uv run pytest` (unit, không cần DB) xanh; guarantee Điều 58 giữ nguyên.

### Tests (viết trước)
- [ ] T009 [P] [US1] Tách/viết `backend/tests/test_vector_store.py`: test **hàm thuần** `hybrid_rank` (IDF/BM25-lite title×3, RRF `rrf_k=60`, guarantee-slot) trên list rows — xác nhận điều khớp tiêu đề (Điều 58) surface dù dense rank thấp; **không cần DB**
- [ ] T010 [P] [US1] Cập nhật `backend/tests/test_rag.py`: thay `FakeCollection` → `FakeVectorRepository`; test `search_stream` dùng repository seam (dense_candidates + all_rows) → hybrid

### Implementation
- [ ] T011 [US1] Refactor `backend/app/services/vector_store.py`: co lại còn **hàm thuần** `hybrid_rank(dense, corpus, query_text, top_k, rrf_k)` (giữ NGUYÊN logic IDF/RRF/guarantee); bỏ `get_client`/`get_collection`/`query_*` gọi Chroma
- [ ] T012 [US1] Hiện thực `PgVectorRepository` trong `backend/app/db/repository.py`: `dense_candidates` (`ORDER BY embedding <=> $1 LIMIT`), `all_rows`, `count`, `upsert_chunks` (`ON CONFLICT (document_id, article_number) DO UPDATE`)
- [ ] T013 [US1] Thêm `get_vector_repository()` (factory theo config) trong `backend/app/db/repository.py` (hoặc `factory.py`); mặc định `PgVectorRepository`
- [ ] T014 [US1] Sửa `backend/app/services/rag.py`: `repo.dense_candidates(q_emb, vector_pool)` + `repo.all_rows()` → `hybrid_rank(...)`; bỏ tham chiếu Chroma; giữ nguyên phần prompt + stream
- [ ] T015 [US1] Chạy `uv run pytest` (unit, không DB) → xanh; xác nhận guarantee Điều 58 qua `FakeVectorRepository`

**Checkpoint**: MVP — truy hồi chạy trên seam repository, logic hybrid giống hệt; unit test xanh không cần Postgres.

---

## Phase 4: User Story 2 — Kho Postgres thống nhất, ingest idempotent (P2)

**Goal**: Nạp dữ liệu thật vào pgvector, chạy lại không nhân bản. **Independent test**: `init_db` + `ingest` → 293 chunk; chạy lại ingest số chunk không đổi.

### Tests (viết trước)
- [ ] T016 [P] [US2] `backend/tests/test_repository.py`: test `upsert_chunks` idempotent + `dense_candidates` trả đúng thứ tự — gắn nhãn integration, **tự `skip` khi thiếu `VN_LEGAL_DATABASE_URL`** (CI nhẹ vẫn xanh)

### Implementation
- [ ] T017 [US2] Tạo `backend/scripts/init_db.py`: runner áp `app/db/schema.sql` (idempotent)
- [ ] T018 [US2] Sửa `backend/scripts/ingest.py`: dùng `repo.upsert_chunks(chunks, embeddings)` thay `delete_collection`/`add_chunks`; giữ chunking/embedding không đổi
- [ ] T019 [US2] Verify local: `docker compose up -d db` → `uv run python scripts/init_db.py` → `uv run python scripts/ingest.py` = **293** chunk; chạy lại → vẫn 293 (idempotent)

**Checkpoint**: Dữ liệu thật nằm trong Postgres+pgvector; ingest tái tạo được.

---

## Phase 5: User Story 3 — Test không cần DB thật (P3)

**Goal**: Toàn bộ suite chạy không cần Postgres. **Independent test**: `pytest` trên máy không có DB → xanh.

- [ ] T020 [P] [US3] Xác nhận `pytest` chạy sạch khi KHÔNG có `VN_LEGAL_DATABASE_URL`: unit dùng `FakeVectorRepository`; `test_repository` tự skip; ghi rõ cơ chế trong `backend/tests/conftest.py`

---

## Phase 6: Polish & Cross-Cutting

- [ ] T021 [P] Rà & gỡ mọi tham chiếu `chromadb`/`chroma_data` còn sót trong mã, scripts, `.gitignore`, docker
- [ ] T022 [P] Cập nhật `backend/.env.example`: thêm `VN_LEGAL_DATABASE_URL`; gỡ biến Chroma
- [ ] T023 [P] Cập nhật `docs/architecture.md`: kho Postgres+pgvector + repository seam (thay sơ đồ ingestion/retrieval ChromaDB)
- [ ] T024 Chạy `uv run ruff check .` + coverage ≥ 80% (`uv run pytest --cov=app`)
- [ ] T025 E2E thủ công với DB thật: 3 acceptance case (Điều 58 / Điều 8&9 / từ chối) tương đương PoC

---

## Dependencies & thứ tự

```
Setup (T001–T004) → Foundational (T005–T008) → US1 (T009–T015) → US2 (T016–T019) → US3 (T020) → Polish (T021–T025)
```

- **US1 = MVP**: logic truy hồi trên seam repository, hành vi giống hệt (test bằng fake, chưa cần DB).
- US2 phụ thuộc US1 (repository + schema) — nạp dữ liệu thật.
- US3 phụ thuộc US1 (seam) — đảm bảo suite độc lập DB.

## Cơ hội chạy song song [P]

- Setup: T003, T004 song song (khác file).
- US1 tests: T009, T010 song song.
- Polish: T021, T022, T023 song song.

## MVP scope

**Chỉ US1 (T001–T015)** = MVP: truy hồi chạy trên `VectorRepository`/`hybrid_rank`, hành vi giống
hệt PoC, unit test xanh không cần DB. US2 (nạp dữ liệu thật) + US3 (test độc lập DB) là increment kế.
