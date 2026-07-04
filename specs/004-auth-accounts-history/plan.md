# Implementation Plan: Auth + tài khoản + lịch sử tra cứu (Supabase)

**Branch**: `004-auth-accounts-history` | **Date**: 2026-07-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-auth-accounts-history/spec.md`

## Summary

Thêm tài khoản + lịch sử tra cứu bằng **Supabase** (local stack qua CLI, offline). Supabase Auth lo
đăng ký/đăng nhập/đăng xuất + phiên (cookie httpOnly qua `@supabase/ssr`). Kho dữ liệu chuyển sang
**Postgres của Supabase** (đưa `legal_chunks` Pha 1 vào; thêm `search_history`), schema quản bằng
**Supabase migrations**. Lịch sử ghi/đọc **client-side qua Supabase + RLS** (`user_id = auth.uid()`) —
FastAPI RAG **không đổi** và không cần biết danh tính. Guest vẫn tra cứu. Đảo D5 của Pha 1 (đưa
Supabase local về sớm; cloud thật vẫn Pha 6).

## Technical Context

**Language/Version**: Python 3.12 (backend, gần như không đổi) · TypeScript/Next.js 16 App Router (frontend)

**Primary Dependencies**: Supabase CLI (local stack) · `@supabase/supabase-js`, `@supabase/ssr` (frontend
— thêm mới) · backend giữ psycopg3/pgvector.

**Storage**: **Postgres của Supabase local** (pgvector). Bảng `legal_chunks` (di trú) + `public.search_history`
(mới, có RLS). Auth: `auth.users`/`auth.sessions` (Supabase quản).

**Testing**: pytest (backend RAG giữ nguyên; integration RLS-isolation) · **Playwright E2E** (frontend:
đăng ký→đăng nhập→tra cứu→lịch sử→cô lập).

**Target Platform**: Dev local (Docker qua Supabase CLI). Cloud để Pha 6.

**Project Type**: Web app (frontend Next.js + backend FastAPI) + Supabase (Auth + Postgres).

**Constraints**: hành vi RAG không đổi (3 acceptance case + Điều 58); mật khẩu do Supabase hash (app
không chạm plaintext); `service_role` không lộ ra client (frontend chỉ `anon key`); cô lập lịch sử bằng RLS.

**Scale/Scope**: chủ yếu **frontend + Supabase migrations**; backend chỉ đổi đích DB + bỏ `init_db/schema.sql`
(thay bằng migrations). Thêm `supabase/` (config + migrations), auth UI, history UI.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Trạng thái |
|-----------|----------|-----------|
| I. Chống bịa | RAG không đổi; verify 3 acceptance case + guarantee Điều 58 | ✅ PASS (gate) |
| II. Verbatim | Dữ liệu điều luật không đổi (chỉ đổi Postgres đích); re-ingest nguyên văn | ✅ PASS |
| III. Test-First & ≥80% | TDD: RLS-isolation test + E2E auth/history viết trước; backend coverage giữ ≥80% | ✅ PASS (gate) |
| IV. Minh bạch | UI "Cơ sở pháp lý"/disclaimer không đổi; thêm trạng thái đăng nhập rõ ràng | ✅ PASS |
| V. Riêng tư/secret | Mật khẩu Supabase hash; **RLS** cô lập lịch sử; anon key ở client, service_role KHÔNG lộ; không log secret | ✅ PASS (gate: rà secret + test cô lập) |
| VI. Đơn giản/abstraction | Dùng Supabase thay vì tự viết auth; backend gần như không đổi | ✅ PASS |

**Kết luận:** Không vi phạm cần biện minh. Ghi chú: đảo D5 (Supabase local về sớm) — đã ghi decision doc,
cloud thật vẫn Pha 6.

## Project Structure

### Documentation (this feature)

```text
specs/004-auth-accounts-history/
├── plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── search-history.md      # bảng + RLS policies + hình dạng bản ghi
│   └── auth-flows.md          # luồng Supabase Auth + ghi lịch sử client-side
└── tasks.md
```

### Source Code (repository root)

```text
supabase/                          # (mới) Supabase local stack
├── config.toml                    # sinh bởi `supabase init`
└── migrations/
    ├── 0001_legal_chunks.sql      # port từ Pha 1 (extension vector + legal_chunks + HNSW)
    └── 0002_search_history.sql    # bảng search_history + RLS + index (user_id, created_at)

backend/
├── app/config.py                  # DATABASE_URL trỏ Postgres Supabase (54322)
├── app/db/schema.sql              # (XOÁ — thay bằng supabase/migrations)
├── scripts/init_db.py             # (XOÁ — migrations lo schema)
└── scripts/ingest.py              # (sửa) bỏ apply_schema; chỉ upsert (bảng do migration tạo)

frontend/
├── package.json                   # (sửa) +@supabase/supabase-js, +@supabase/ssr, +@playwright/test (dev)
├── middleware.ts                  # (mới) refresh phiên Supabase (httpOnly cookie)
├── lib/supabase/
│   ├── client.ts                  # browser client (anon key)
│   └── server.ts                  # server client (cookies)
├── lib/history.ts                 # (mới) ghi/đọc search_history qua Supabase client
├── components/auth/
│   ├── AuthForm.tsx               # đăng ký/đăng nhập (email+mật khẩu)
│   └── UserMenu.tsx               # trạng thái đăng nhập + đăng xuất
├── components/layout/Header.tsx   # (mới) header + UserMenu
├── app/login/page.tsx             # trang đăng nhập/đăng ký
├── app/history/page.tsx           # xem lịch sử của mình
├── app/layout.tsx                 # (sửa) thêm Header
├── hooks/useStreamQuery.ts        # (sửa) sau 'done' + đã đăng nhập → ghi lịch sử
└── tests/e2e/auth-history.spec.ts # (mới) Playwright: register→login→search→history→isolation

.env.local (frontend)              # NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY (từ `supabase start`)
docker-compose.yml                 # (sửa) bỏ service db thuần; Supabase stack chạy qua CLI
```

**Structure Decision**: Supabase là kho + auth thống nhất. Backend RAG giữ nguyên (chỉ đổi đích DB, bỏ
init_db/schema.sql → migrations). Auth + lịch sử là **frontend + Supabase (RLS)**; FastAPI không gác auth.

## Ghi chú kỹ thuật then chốt
- **RLS**: `search_history` bật RLS; policy `select/insert/delete USING (user_id = auth.uid())`;
  `user_id uuid default auth.uid() references auth.users(id)`. Cô lập ở tầng DB (SC-004).
- **Ghi lịch sử**: sau sự kiện SSE `done`, nếu có phiên → `supabase.from('search_history').insert({query, sources})`
  (user_id tự = auth.uid()). Guest bỏ qua.
- **Phiên**: `@supabase/ssr` + `middleware.ts` refresh; cookie httpOnly. Frontend chỉ dùng **anon key**.
- **Migrations = nguồn schema**: `supabase db reset` áp toàn bộ; ingest chỉ upsert. Re-ingest 293 chunk.
- **Bí mật**: `service_role` (từ `supabase start`) KHÔNG đưa vào frontend; nếu backend cần thao tác admin
  (không bắt buộc ở Pha 2) thì để ở env backend, không log.

## Complexity Tracking

> Không có vi phạm Constitution cần biện minh. Việc thay hạ tầng Pha 1 (pgvector docker → Supabase local)
> là hệ quả trực tiếp của quyết định sản phẩm (kho thống nhất), không phải phức tạp thừa.
