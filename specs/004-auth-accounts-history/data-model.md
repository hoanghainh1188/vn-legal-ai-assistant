# Data Model (Phase 1): search_history (+ legal_chunks giữ nguyên)

**Feature**: `004-auth-accounts-history` | **Date**: 2026-07-04

## `auth.users` / `auth.sessions` — do Supabase quản
Không tự tạo. `search_history.user_id` tham chiếu `auth.users(id)` (uuid).

## `public.search_history` (mới)

| Cột | Kiểu | Ràng buộc | Ghi chú |
|-----|------|-----------|---------|
| `id` | `bigint generated always as identity` | PK | |
| `user_id` | `uuid` | NOT NULL, default `auth.uid()`, FK `auth.users(id)` on delete cascade | chủ sở hữu |
| `query` | `text` | NOT NULL, check `char_length ≤ 500` | câu hỏi |
| `sources` | `jsonb` | NOT NULL default `'[]'` | `[{document_id, article_number, article_title}]` |
| `created_at` | `timestamptz` | NOT NULL default `now()` | thời điểm |

**Index**: `(user_id, created_at desc)` — liệt kê lịch sử của user, mới nhất trước.

**RLS** (bật): mọi thao tác chỉ trên hàng `user_id = auth.uid()`.

## DDL — `supabase/migrations/0002_search_history.sql`

```sql
create table if not exists public.search_history (
    id         bigint generated always as identity primary key,
    user_id    uuid not null default auth.uid() references auth.users (id) on delete cascade,
    query      text not null check (char_length(query) <= 500),
    sources    jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists search_history_user_created_idx
    on public.search_history (user_id, created_at desc);

alter table public.search_history enable row level security;

create policy "history_select_own" on public.search_history
    for select using (user_id = auth.uid());
create policy "history_insert_own" on public.search_history
    for insert with check (user_id = auth.uid());
create policy "history_delete_own" on public.search_history
    for delete using (user_id = auth.uid());
```

## `legal_chunks` — `supabase/migrations/0001_legal_chunks.sql`
Port nguyên từ Pha 1 (`app/db/schema.sql`): extension `vector`, bảng `legal_chunks`
(`UNIQUE(document_id, article_number)`), index HNSW `vector_cosine_ops`. **Không** bật RLS (đọc/ghi
qua backend bằng kết nối trực tiếp; frontend không truy cập trực tiếp legal_chunks).

## Bất biến
- `search_history.user_id` luôn = chủ phiên (RLS ép); guest không tạo được hàng.
- `sources` chỉ chứa tham chiếu điều (không lưu toàn văn câu trả lời — D6).
- `legal_chunks`: 293 hàng sau re-ingest; hành vi RAG không đổi.
