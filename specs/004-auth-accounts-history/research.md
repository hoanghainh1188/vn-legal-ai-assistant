# Research (Phase 0): Supabase local stack + Auth + RLS

**Feature**: `004-auth-accounts-history` | **Date**: 2026-07-04

Quyết định đã chốt ở clarify: `docs/04-decisions/2026-07-04-feature-004-auth-supabase.md`.

## R1 — Supabase local stack (CLI)
- **Quyết định**: `supabase init` tạo `supabase/`; `supabase start` chạy Docker stack (Postgres+pgvector,
  GoTrue auth, PostgREST, Studio, Inbucket mail). Postgres local mặc định cổng **54322**, API **54321**.
- **Đã xác minh**: `supabase` CLI 2.109.0 + Docker 29 có sẵn.
- **Biến từ output `supabase start`**: `API URL` (54321) → `NEXT_PUBLIC_SUPABASE_URL`; `anon key` →
  `NEXT_PUBLIC_SUPABASE_ANON_KEY`; `DB URL` (54322) → backend `VN_LEGAL_DATABASE_URL`. `service_role key`
  giữ bí mật (không đưa frontend).

## R2 — Migrations là nguồn schema
- **Quyết định**: `supabase/migrations/0001_legal_chunks.sql` (port từ `app/db/schema.sql` Pha 1) +
  `0002_search_history.sql`. Áp bằng `supabase db reset` (local) — idempotent theo version.
- **Hệ quả**: bỏ `backend/app/db/schema.sql` + `scripts/init_db.py`; `ingest.py` bỏ `apply_schema()`.
- **pgvector trong Supabase**: bật bằng `create extension if not exists vector;` trong migration 0001
  (Supabase image có sẵn extension).

## R3 — Auth qua `@supabase/ssr` (Next.js App Router)
- **Quyết định**: dùng `@supabase/ssr` tạo browser client (`lib/supabase/client.ts`) + server client
  (`lib/supabase/server.ts` đọc/ghi cookies) + `middleware.ts` gọi `supabase.auth.getUser()` để refresh
  phiên. Cookie **httpOnly** do helper quản.
- **Luồng**: `supabase.auth.signUp/signInWithPassword/signOut`. Mật khẩu do GoTrue hash (app không chạm).
- **Lý do**: chuẩn chính thức Supabase cho App Router; tránh lộ token cho JS (an toàn XSS).

## R4 — RLS cô lập lịch sử
- **Quyết định**: `search_history` bật RLS; `user_id uuid not null default auth.uid() references auth.users(id)
  on delete cascade`. Policies:
  - `select`: `using (user_id = auth.uid())`
  - `insert`: `with check (user_id = auth.uid())`
  - `delete`: `using (user_id = auth.uid())`
- **Lý do**: cô lập ở **tầng DB** — kể cả gọi thẳng PostgREST vẫn không đọc được hàng người khác (SC-004).
- **Frontend**: dùng anon key + JWT của user → RLS áp `auth.uid()` tự động.

## R5 — Backend RAG giữ nguyên
- **Quyết định**: FastAPI `/api/query` + repository psycopg3 **không đổi**, chỉ trỏ `DATABASE_URL` sang
  Postgres của Supabase. Kết nối trực tiếp (superuser/postgres role) **bỏ qua RLS** → ingest/RAG legal_chunks
  không bị RLS chặn (legal_chunks không bật RLS; đọc qua backend).
- **Re-ingest**: chạy lại `ingest.py` để nạp 293 chunk vào Postgres của Supabase.

## R6 — Ghi lịch sử client-side
- **Quyết định**: sau sự kiện SSE `done`, nếu có phiên, frontend `supabase.from('search_history').insert(
  { query, sources })`. `user_id` tự = `auth.uid()` (default). Guest: bỏ qua.
- **Lý do**: backend không cần biết danh tính (FR-006); tách bạch RAG khỏi auth.

## R7 — Testing
- **Backend**: giữ 38 test (RAG không đổi); integration test cô lập RLS: tạo 2 user (Supabase admin API
  qua service_role trong test env), insert history mỗi user, xác nhận mỗi JWT chỉ đọc hàng của mình.
  Skip khi thiếu Supabase local (giống test_repository).
- **Frontend**: **Playwright E2E** happy-path: đăng ký → đăng nhập → tra cứu → thấy lịch sử; +1 case
  cô lập (2 tài khoản). Đây là lưới chính cho logic mới (web testing rules ưu tiên E2E cho frontend).
- **Không hồi quy**: 3 acceptance case RAG chạy lại sau khi đổi DB đích.
