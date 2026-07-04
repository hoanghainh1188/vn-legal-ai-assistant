# Quickstart (Phase 1): Supabase local + Auth + lịch sử

**Feature**: `004-auth-accounts-history` | **Date**: 2026-07-04

## 1. Khởi Supabase local stack

```bash
# từ root repo (đã có supabase/ sau `supabase init`)
supabase start           # Docker: Postgres+pgvector, Auth, Studio, Inbucket
supabase db reset        # áp toàn bộ migrations (legal_chunks + search_history + RLS)
```

`supabase start` in ra: `API URL` (54321), `anon key`, `service_role key`, `DB URL` (54322).

## 2. Cấu hình biến môi trường

```bash
# backend/.env
VN_LEGAL_DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres

# frontend/.env.local
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon key từ supabase start>
```

> `service_role key` KHÔNG đưa vào frontend. Chỉ dùng ở test/backend nếu cần thao tác admin.

## 3. Nạp dữ liệu pháp lý (vào Postgres của Supabase)

```bash
cd backend
uv run python scripts/ingest.py      # upsert 293 chunk (bảng do migration tạo sẵn)
```

## 4. Chạy app

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev     # cài @supabase/ssr, @supabase/supabase-js
```

Kiểm thủ công:
- Guest tra cứu 3 acceptance case (Điều 58 / Điều 8&9 / từ chối) — không đổi.
- Đăng ký → đăng nhập → tra cứu → mở **/history** thấy lượt vừa hỏi.
- Đăng nhập tài khoản khác → chỉ thấy lịch sử của mình.

## 5. Test

```bash
# Backend (RAG không đổi + RLS isolation nếu có Supabase)
cd backend && uv run pytest --cov=app          # ≥80%
# E2E frontend (Supabase local + backend đang chạy)
cd frontend && npx playwright test
```

## Definition of Done
- [ ] `supabase start` + `db reset` → migrations áp (legal_chunks + search_history + RLS).
- [ ] Re-ingest 293 chunk vào Postgres Supabase; 3 acceptance case không đổi.
- [ ] Đăng ký/đăng nhập/đăng xuất chạy; phiên trong cookie httpOnly.
- [ ] Đã đăng nhập tra cứu → có bản ghi lịch sử; guest → không; xem lại đúng của mình.
- [ ] Cô lập RLS: user A không thấy lịch sử user B (test).
- [ ] Không hardcode/không log secret; `service_role` không lộ frontend; backend coverage ≥80%.
