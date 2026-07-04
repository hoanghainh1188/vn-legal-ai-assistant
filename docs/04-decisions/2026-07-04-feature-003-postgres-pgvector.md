# Quyết định — Feature #3 (Pha 1): Migrate ChromaDB → Postgres + pgvector

**Ngày**: 2026-07-04
**Feature**: `003-postgres-pgvector` (issue #3, roadmap epic #2 — Pha 1)
**Trạng thái**: đã chốt qua `speckit-clarify`

Ghi lại các câu trả lời ambiguity của Pha 1 (theo Quy tắc bắt buộc #2). Tham chiếu:
`specs/003-postgres-pgvector/spec.md`.

## D1 — Tầng truy cập Postgres: **psycopg3 async + raw SQL**
- **Chọn**: `psycopg` (v3) async + `pgvector` register adapter; SQL viết tay. KHÔNG dùng ORM.
- **Lý do**: Constitution VI (đơn giản, ít abstraction thừa). Codebase hiện thuần `httpx`, không
  ORM; migration này chỉ cần vài truy vấn (upsert, similarity, fetch-all cho lexical).
- **Loại bỏ**: SQLAlchemy — thêm lớp trừu tượng & phụ thuộc chưa cần ở Pha 1. Cân nhắc lại nếu Pha 2
  (users/history) khiến quan hệ phức tạp lên.

## D2 — Lexical retrieval: **giữ IDF/BM25-lite trong Python**
- **Chọn**: Truy hồi lấy các rows ứng viên từ Postgres (dense qua pgvector + toàn bộ chunk cho lexical
  scoring), rồi tính IDF/BM25-lite + RRF + guarantee **trong Python** như hiện tại.
- **Lý do**: Bảo toàn HỆT hành vi (title ×3, guarantee-slot đưa Điều 58 lên dù dense rank thấp). 293
  rows nên chi phí fetch-all không đáng kể. Constitution I (không hồi quy chất lượng truy hồi).
- **Loại bỏ**: Postgres FTS (tsvector/ts_rank) — tiếng Việt cần `unaccent` + text search config riêng,
  và khó tái tạo chính xác logic title×3/guarantee → rủi ro hồi quy. Để dành tối ưu ở pha sau nếu scale.

## D3 — Kiểm thử: **repository seam** (`VectorRepository` protocol)
- **Chọn**: Tách logic hybrid (hàm thuần trên rows) khỏi tầng DB qua `VectorRepository` protocol +
  `PgVectorRepository`. Unit test tiêm repository giả (fake rows) → chạy **không cần Postgres thật**.
- **Lý do**: Constitution III (test-first, vòng lặp nhanh, CI nhẹ) + FR-008. Cùng pattern provider của
  Pha 0 (`app/providers/`).
- **e2e/ingest local**: dùng pgvector qua Docker (`docker compose`).

## D4 — Migration schema: **file SQL versioned + runner nhỏ**
- **Chọn**: Một/nhiều file `.sql` (extension `vector`, bảng `legal_chunks`, index HNSW) + script apply
  nhỏ (idempotent, `CREATE ... IF NOT EXISTS`).
- **Lý do**: Đủ cho Pha 1, minh bạch, không thêm phụ thuộc. 
- **Loại bỏ**: Alembic/yoyo — nâng cấp ở Pha 6 nếu vòng đời schema cần version/rollback bài bản.

## D5 — Supabase cloud: **hoãn tới Pha 6**
- **Chọn**: Pha 1 chỉ dùng **pgvector cục bộ** (`pgvector/pgvector:pg16` qua Docker). Không kết nối
  Supabase cloud thật.
- **Lý do**: Tách bạch migration code (Pha 1) khỏi wiring hạ tầng/secret cloud (Pha 6). pgvector local
  cùng engine nên tương thích Supabase — không phải làm lại khi lên cloud.

## Tham số kỹ thuật kèm theo (không đổi so với PoC)
- Embedding: bge-m3 **1024 chiều**, khoảng cách **cosine** (pgvector `<=>`, index HNSW `vector_cosine_ops`).
- Metadata mỗi chunk: `article_number, article_title, document_id, chapter, content`.
- Biến môi trường mới: `VN_LEGAL_DATABASE_URL` (tài liệu hoá trong `.env.example`).
