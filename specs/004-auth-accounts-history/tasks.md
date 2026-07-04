# Tasks: Auth + tài khoản + lịch sử tra cứu (Supabase)

**Feature**: `004-auth-accounts-history` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Tests**: BẮT BUỘC (Constitution III). E2E/integration viết trước implementation (RED → GREEN).

**Format**: `- [ ] [TaskID] [P?] [Story?] Mô tả + đường dẫn`

---

## Phase 1: Setup

- [ ] T001 `supabase init` → tạo `supabase/` + `config.toml` (bật auth email, tắt confirm email cho local)
- [ ] T002 `supabase/migrations/0001_legal_chunks.sql` — port từ `backend/app/db/schema.sql` (extension vector + legal_chunks + HNSW)
- [ ] T003 `supabase/migrations/0002_search_history.sql` — bảng + RLS + index theo [data-model.md](./data-model.md)
- [ ] T004 [P] Frontend deps: `npm i @supabase/supabase-js @supabase/ssr` + `npm i -D @playwright/test`
- [ ] T005 Backend: `config.py` DATABASE_URL trỏ Supabase (54322); **xoá** `backend/app/db/schema.sql` + `backend/scripts/init_db.py`; `scripts/ingest.py` bỏ `apply_schema()` (bảng do migration tạo)
- [ ] T006 `docker-compose.yml`: bỏ service `db` thuần (Supabase CLI thay); giữ backend (hoặc ghi chú chạy qua supabase)

## Phase 2: Foundational (chặn tất cả user story)

- [ ] T007 `supabase start` + `supabase db reset` → verify `legal_chunks`, `public.search_history` (RLS bật) tồn tại
- [ ] T008 Re-ingest: `uv run python scripts/ingest.py` → 293 chunk vào Postgres Supabase; verify 3 acceptance case không đổi
- [ ] T009 Frontend Supabase clients: `lib/supabase/client.ts`, `lib/supabase/server.ts`, `middleware.ts` (refresh phiên httpOnly) theo [contracts/auth-flows.md](./contracts/auth-flows.md)

---

## Phase 3: User Story 1 — Đăng ký/đăng nhập/đăng xuất (P1) 🎯 MVP

**Goal**: Người dùng có tài khoản + phiên. **Independent test**: đăng ký → đăng xuất → đăng nhập lại; sai mật khẩu bị từ chối.

### Tests (viết trước)
- [ ] T010 [P] [US1] Playwright E2E `frontend/tests/e2e/auth.spec.ts`: đăng ký → thấy đã đăng nhập → đăng xuất → đăng nhập lại; sai mật khẩu → lỗi chung

### Implementation
- [ ] T011 [US1] `components/auth/AuthForm.tsx` — form đăng ký/đăng nhập (email+mật khẩu; validate; lỗi chung, không tiết lộ email tồn tại) dùng `supabase.auth.signUp/signInWithPassword`
- [ ] T012 [US1] `components/auth/UserMenu.tsx` + `components/layout/Header.tsx` — hiển thị email + nút đăng xuất (`signOut`); guest thấy nút Đăng nhập
- [ ] T013 [US1] `app/login/page.tsx` + gắn `Header` vào `app/layout.tsx`
- [ ] T014 [US1] Chạy `npx playwright test auth` → xanh

**Checkpoint**: MVP — tài khoản + phiên hoạt động; trang tra cứu vẫn dùng được (guest).

---

## Phase 4: User Story 2 — Tự lưu lịch sử tra cứu (P2)

**Goal**: Lượt tra cứu của người đăng nhập được lưu; guest không. **Independent test**: đăng nhập tra cứu → có bản ghi; guest → không; RAG không đổi.

### Tests (viết trước)
- [ ] T015 [P] [US2] Integration RLS-isolation `backend/tests/test_rls_isolation.py` (skip nếu thiếu Supabase): tạo 2 user (service_role), insert history mỗi user, xác nhận mỗi JWT chỉ đọc hàng của mình
- [ ] T016 [P] [US2] E2E `frontend/tests/e2e/history.spec.ts` (phần lưu): đăng nhập → tra cứu → 1 bản ghi xuất hiện; guest tra cứu → 0 bản ghi

### Implementation
- [ ] T017 [US2] `lib/history.ts` — `saveHistory(query, sources)` insert qua Supabase (guest bỏ qua); kiểu `SourceRef = {document_id, article_number, article_title}`
- [ ] T018 [US2] `hooks/useStreamQuery.ts` — sau sự kiện SSE `done`, nếu đã đăng nhập → `saveHistory(query, sources)` (không đổi luồng câu trả lời)
- [ ] T019 [US2] Verify: lịch sử ghi khi đăng nhập, guest không; 3 acceptance case RAG vẫn xanh

**Checkpoint**: Lịch sử tự lưu cho người đăng nhập; guest tra cứu nguyên vẹn.

---

## Phase 5: User Story 3 — Xem lại lịch sử của mình (P3)

**Goal**: Xem danh sách lịch sử của chính mình. **Independent test**: 2 tài khoản, mỗi bên chỉ thấy của mình.

### Tests (viết trước)
- [ ] T020 [P] [US3] E2E `frontend/tests/e2e/history.spec.ts` (phần xem): mở /history thấy lượt của mình; tài khoản B không thấy của A

### Implementation
- [ ] T021 [US3] `app/history/page.tsx` — đọc `search_history` qua Supabase (mới nhất trước; RLS tự lọc); link từ `Header`
- [ ] T022 [US3] Chạy `npx playwright test history` → xanh (gồm cô lập)

---

## Phase 6: Polish & Cross-Cutting

- [ ] T023 [P] `frontend/.env.local.example` (NEXT_PUBLIC_SUPABASE_URL/ANON_KEY) + `backend/.env.example` (DATABASE_URL Supabase) — KHÔNG secret thật, ghi rõ lấy từ `supabase start`
- [ ] T024 [P] `docs/architecture.md`: thêm Supabase (Auth + `search_history` + RLS + luồng ghi lịch sử client-side)
- [ ] T025 [P] `README.md` + `CLAUDE.md`: cập nhật tech stack (Supabase) + quy trình chạy (`supabase start`)
- [ ] T026 Backend `uv run pytest --cov=app` ≥80% (RAG không đổi) + `ruff check` sạch
- [ ] T027 E2E thủ công: 3 acceptance case RAG trên Postgres Supabase (không hồi quy)

---

## Dependencies & thứ tự

```
Setup (T001–T006) → Foundational (T007–T009) → US1 (T010–T014) → US2 (T015–T019) → US3 (T020–T022) → Polish (T023–T027)
```

- **US1 = MVP**: tài khoản + phiên. US2 cần US1 (danh tính) + T009 (clients). US3 cần US2 (có dữ liệu).
- Backend RAG không đổi → 38 test cũ giữ xanh xuyên suốt.

## Cơ hội chạy song song [P]

- Setup: T004 song song T002/T003.
- Tests: T010, T015, T016, T020 (khác file) song song khi tới phase tương ứng.
- Polish: T023, T024, T025 song song.

## MVP scope

**US1 (T001–T014)** = MVP: có tài khoản + phiên, trang tra cứu vẫn dùng được cho guest. US2 (lưu lịch
sử) + US3 (xem lịch sử) là increment kế tiếp.
