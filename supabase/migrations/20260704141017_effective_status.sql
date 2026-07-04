-- Metadata hiệu lực CẤP VĂN BẢN (denormalized vào legal_chunks) — Feature #7.
-- Nguồn: manifest sources.py (xác minh từ API MOJ). Chỉ cấp văn bản, không cấp điều.

alter table public.legal_chunks
    add column if not exists document_name text,
    add column if not exists eff_status   text,
    add column if not exists eff_date      date;
