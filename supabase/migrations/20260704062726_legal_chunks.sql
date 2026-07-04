-- Kho vector Luật Nhà ở — port từ Pha 1 (backend/app/db/schema.sql).
-- Đọc/ghi qua backend (kết nối trực tiếp), KHÔNG bật RLS; frontend không truy cập bảng này.

create extension if not exists vector;

create table if not exists public.legal_chunks (
    id             bigint generated always as identity primary key,
    document_id    text         not null,
    article_number int          not null,
    article_title  text         not null,
    chapter        text         not null,
    content        text         not null,      -- nguyên văn Điều (Constitution II)
    embedding      vector(1024) not null,       -- bge-m3, cosine
    unique (document_id, article_number)        -- khoá tự nhiên cho upsert idempotent
);

create index if not exists legal_chunks_embedding_hnsw
    on public.legal_chunks using hnsw (embedding vector_cosine_ops);

-- Defense-in-depth: bật RLS (deny-all mặc định, không policy nào) để lỡ có ai GRANT
-- cho anon/authenticated thì PostgREST vẫn không đọc được. Backend dùng superuser
-- (kết nối trực tiếp) nên KHÔNG bị ảnh hưởng — RAG/ingest hoạt động bình thường.
alter table public.legal_chunks enable row level security;
