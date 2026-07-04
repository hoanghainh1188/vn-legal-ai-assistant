# Contract: search_history (bảng + RLS + shape)

**Feature**: `004-auth-accounts-history` | **Date**: 2026-07-04

Nguồn schema: `supabase/migrations/*_search_history.sql`. Chi tiết cột: [../data-model.md](../data-model.md).

## Bảng `public.search_history`

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | `bigint identity` PK | |
| `user_id` | `uuid` default `auth.uid()` → `auth.users(id)` on delete cascade | chủ sở hữu |
| `query` | `text` (≤ 500) | câu hỏi |
| `sources` | `jsonb` default `[]` | `SourceRef[]` |
| `created_at` | `timestamptz` default `now()` | |

`SourceRef = { document_id: string; article_number: number; article_title: string }`.

## Bảo mật (RLS + grant)

```sql
alter table public.search_history enable row level security;
grant select, insert, delete on public.search_history to authenticated;  -- anon KHÔNG có quyền

create policy "history_select_own" ... using (user_id = auth.uid());
create policy "history_insert_own" ... with check (user_id = auth.uid());
create policy "history_delete_own" ... using (user_id = auth.uid());
```

- **Cô lập**: mọi thao tác chỉ trên hàng `user_id = auth.uid()`. Guest (anon) không có grant → không đọc/ghi.
- Kiểm chứng: `backend/tests/test_rls_isolation.py` (user A không đọc được hàng user B, và ngược lại).

## Hợp đồng truy cập (frontend, qua Supabase client + RLS)

| Thao tác | Gọi | Ai |
|----------|-----|-----|
| Ghi | `supabase.from("search_history").insert({ query, sources })` (`user_id` tự = `auth.uid()`) | đã đăng nhập (guest bỏ qua) — `lib/history.ts` |
| Đọc | `supabase.from("search_history").select("id, query, sources, created_at").order("created_at", { ascending: false })` | đã đăng nhập — `app/history/page.tsx` |

Không có endpoint FastAPI cho lịch sử — RLS là lớp cô lập duy nhất & đủ.
