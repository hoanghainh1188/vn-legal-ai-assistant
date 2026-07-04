# Implementation Plan: Migrate kho vector sang Postgres + pgvector

**Branch**: `003-postgres-pgvector` | **Date**: 2026-07-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-postgres-pgvector/spec.md`

## Summary

Thay kho vector **ChromaDB local** bằng **Postgres + pgvector**, giữ **hệt** hành vi truy hồi
(dense cosine + lexical IDF/BM25-lite title×3 + RRF + guarantee Điều 58). Tách logic hybrid (hàm
thuần trên rows) khỏi tầng dữ liệu qua `VectorRepository` protocol + `PgVectorRepository` (psycopg3
async + pgvector), để unit test chạy **không cần** Postgres thật. Cập nhật `ingest.py` (upsert
idempotent), `config.py` (`VN_LEGAL_DATABASE_URL`), `docker-compose.yml` (service pgvector), gỡ
`chromadb`. Schema qua file SQL versioned + runner nhỏ. Supabase cloud hoãn Pha 6.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI, httpx (Ollama), `psycopg[binary]` (v3, async — thêm mới),
`pgvector` (adapter — thêm mới), pydantic-settings. **Gỡ**: `chromadb`.

**Storage**: **Postgres + pgvector** (thay ChromaDB). Cột `embedding vector(1024)`, index HNSW
`vector_cosine_ops`, toán tử cosine `<=>`. Bảng `legal_chunks`.

**Testing**: pytest (+ pytest-asyncio). Unit test truy hồi dùng **repository giả** (không DB thật).
Ingest/e2e local dùng pgvector qua Docker.

**Target Platform**: Linux server (backend managed) / dev local (Docker Compose).

**Project Type**: Web service (backend của web app frontend+backend).

**Performance Goals**: Không đổi cảm nhận người dùng. 293 chunk — fetch-all cho lexical không đáng kể.
Similarity qua index HNSW.

**Constraints**: Hành vi RAG giữ nguyên (3 acceptance case + guarantee Điều 58); hợp đồng `/api/query`
và SSE không đổi; không hardcode/không log secret (connection string); test chạy không cần DB thật.

**Scale/Scope**: Refactor tầng lưu trữ. Sửa `vector_store.py` (→ repository), `rag.py`, `ingest.py`,
`config.py`; thêm `db/` (connection + repository + schema SQL + runner); `docker-compose.yml`,
`pyproject.toml`, `.env.example`. Không đổi frontend.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Trạng thái |
|-----------|----------|-----------|
| I. Chống bịa | Giữ HỆT retrieval hybrid + guarantee Điều 58; verify 3 acceptance case + test guarantee | ✅ PASS (gate: 3 case + test guarantee xanh) |
| II. Verbatim | `content` chunk lưu nguyên văn; ingest chỉ đổi đích lưu, không đổi text | ✅ PASS |
| III. Test-First & ≥80% | TDD: viết test repository-fake + hybrid trước; port test hiện có sang seam | ✅ PASS (gate) |
| IV. Minh bạch | UI/luồng "Cơ sở pháp lý" không đổi | ✅ PASS (N/A) |
| V. Riêng tư/secret | `DATABASE_URL` qua env, không log connection string | ✅ PASS (gate: rà soát không log secret) |
| VI. Đơn giản/abstraction | psycopg3 + SQL thuần (không ORM); repository seam tối thiểu, đúng nhu cầu | ✅ PASS |

**Kết luận:** Không có vi phạm cần biện minh → Complexity Tracking để trống.

## Project Structure

### Documentation (this feature)

```text
specs/003-postgres-pgvector/
├── plan.md              # File này
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (schema legal_chunks)
├── quickstart.md        # Phase 1 output (chạy DB + ingest + test)
├── contracts/           # Phase 1 output
│   └── vector-repository.md   # Hợp đồng VectorRepository
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/app/
├── config.py                  # (sửa) thêm database_url (VN_LEGAL_DATABASE_URL)
├── db/                        # (mới) tầng dữ liệu Postgres
│   ├── __init__.py
│   ├── connection.py          # async pool psycopg3 + register pgvector; fail-fast nếu thiếu config
│   ├── repository.py          # VectorRepository protocol + PgVectorRepository
│   └── schema.sql             # extension vector + bảng legal_chunks + index HNSW (idempotent)
├── services/
│   ├── vector_store.py        # (sửa) chỉ còn HÀM THUẦN hybrid (RRF/lexical) trên rows; bỏ Chroma
│   └── rag.py                 # (sửa) dùng repository + hàm hybrid; bỏ get_client/get_collection Chroma
└── ...

backend/scripts/
├── ingest.py                  # (sửa) upsert idempotent qua repository (thay delete_collection/add_chunks)
└── init_db.py                 # (mới) runner áp schema.sql (idempotent)

backend/tests/
├── test_rag.py                # (sửa) FakeCollection → FakeVectorRepository; giữ test hybrid/guarantee
├── test_vector_store.py       # (mới/tách) test hàm thuần RRF/lexical trên rows (không DB)
├── test_repository.py         # (mới) test PgVectorRepository qua psycopg mock / hoặc gắn nhãn integration
└── (giữ) test_providers.py, test_claude_provider.py, test_chunking.py, test_query.py

backend/pyproject.toml         # (sửa) +psycopg[binary], +pgvector ; −chromadb
backend/.env.example           # (sửa) thêm VN_LEGAL_DATABASE_URL
docker-compose.yml             # (sửa) thêm service db (pgvector/pgvector:pg16) + volume; bỏ volume chroma
```

**Structure Decision**: Giữ backend web service hiện có. Thêm package `backend/app/db/` gói toàn
bộ chi tiết Postgres (connection + repository + schema). `services/vector_store.py` co lại còn
**logic hybrid thuần** (dễ test, tái dùng). `rag.py`/`ingest.py` phụ thuộc `VectorRepository` (seam),
không biết Postgres cụ thể — cùng tinh thần package `providers/` của Pha 0. Frontend không đổi.

## Complexity Tracking

> Không có vi phạm Constitution → không cần biện minh độ phức tạp.
