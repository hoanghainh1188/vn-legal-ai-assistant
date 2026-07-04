# Data Model (Phase 1): legal_chunks

**Feature**: `003-postgres-pgvector` | **Date**: 2026-07-04

## Bảng `legal_chunks`

| Cột | Kiểu | Ràng buộc | Ghi chú |
|-----|------|-----------|---------|
| `id` | `bigserial` | PK | khóa nội bộ |
| `document_id` | `text` | NOT NULL | vd `27/2023/QH15`, `95/2024/ND-CP` |
| `article_number` | `int` | NOT NULL | số Điều |
| `article_title` | `text` | NOT NULL | tiêu đề Điều (dùng cho lexical title×3) |
| `chapter` | `text` | NOT NULL | số chương (La Mã) |
| `content` | `text` | NOT NULL | **nguyên văn** Điều (Constitution II) |
| `embedding` | `vector(1024)` | NOT NULL | bge-m3, cosine |

**Khóa tự nhiên (idempotent upsert)**: `UNIQUE (document_id, article_number)`.

**Index**:
- `USING hnsw (embedding vector_cosine_ops)` — truy vấn ANN cosine.
- (tùy chọn) `(document_id, article_number)` do UNIQUE tự tạo.

## DDL (idempotent — `app/db/schema.sql`)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS legal_chunks (
    id             bigserial PRIMARY KEY,
    document_id    text        NOT NULL,
    article_number int         NOT NULL,
    article_title  text        NOT NULL,
    chapter        text        NOT NULL,
    content        text        NOT NULL,
    embedding      vector(1024) NOT NULL,
    UNIQUE (document_id, article_number)
);

CREATE INDEX IF NOT EXISTS legal_chunks_embedding_hnsw
    ON legal_chunks USING hnsw (embedding vector_cosine_ops);
```

## Ánh xạ sang `SourceDocument` (không đổi hợp đồng phía trên)

`SourceDocument` hiện có (metadata trả cho RAG) giữ nguyên các trường:
`article_number, article_title, document_id, chapter, content`. Repository trả list dict/row map
1-1 với các cột trên; logic hybrid tính điểm rồi dựng `SourceDocument` như hiện tại.

## Bất biến (invariants)
- Số chiều `embedding` = **1024**; ghi vector khác chiều → lỗi (FR + edge case).
- `content` lưu **nguyên văn**, không cắt/không sửa (Constitution II).
- Tổng số bản ghi sau ingest = **293** (198 + 95).
- Upsert theo `(document_id, article_number)` → chạy lại ingest không nhân bản.

## Phạm vi tương lai (ngoài Pha 1)
- Bảng `users`, `search_history` (Pha 2) sẽ cùng DB này — lý do chọn kho quan hệ thống nhất.
