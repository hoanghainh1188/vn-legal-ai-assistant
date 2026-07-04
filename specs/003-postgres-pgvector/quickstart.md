# Quickstart (Phase 1): Postgres + pgvector

**Feature**: `003-postgres-pgvector` | **Date**: 2026-07-04

## 1. Khởi Postgres + pgvector (local)

```bash
# từ root repo
docker compose up -d db          # service db: pgvector/pgvector:pg16
```

## 2. Cấu hình

```bash
# backend/.env  (mẫu ở .env.example)
VN_LEGAL_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vn_legal
```

## 3. Tạo schema + nạp dữ liệu

```bash
cd backend
uv run python scripts/init_db.py     # áp app/db/schema.sql (idempotent)
uv run python scripts/ingest.py      # nạp 293 chunk (198 + 95) — chạy lại được, không nhân bản
```

Kỳ vọng: `Ingestion complete — 293 chunks from 2 documents.`

## 4. Chạy backend + kiểm thử thủ công

```bash
uv run uvicorn app.main:app --reload --port 8000
```

3 acceptance case (tương đương PoC):
1. "Chung cư có thời hạn sở hữu tối đa bao nhiêu năm?" → trích **Điều 58**.
2. "Việt kiều mua nhà ở VN được không?" → trích **Điều 8 & 9**.
3. "Lái xe quá tốc độ bị phạt bao nhiêu?" → từ chối an toàn.

## 5. Test (không cần Postgres)

```bash
cd backend
uv run pytest              # unit test hybrid/guarantee dùng FakeVectorRepository → không cần DB
uv run pytest --cov=app    # coverage ≥ 80%
```

> Test kết nối thật (`test_repository`) tự bỏ qua khi không có `VN_LEGAL_DATABASE_URL`.

## Definition of Done
- [ ] `pytest` xanh, coverage ≥ 80%, không cần DB thật cho unit test.
- [ ] `ingest.py` nạp 293 chunk vào Postgres; chạy lại không nhân bản.
- [ ] 3 acceptance case tương đương PoC (Điều 58 vẫn surface).
- [ ] `chromadb` đã gỡ khỏi `pyproject.toml` và mã.
- [ ] `VN_LEGAL_DATABASE_URL` có trong `.env.example`; không hardcode/không log secret.
