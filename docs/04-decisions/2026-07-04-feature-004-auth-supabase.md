# Quyết định — Feature #4 (Pha 2): Auth + tài khoản + lịch sử tra cứu

**Ngày**: 2026-07-04
**Feature**: `004-auth-accounts-history` (issue #4, roadmap epic #2 — Pha 2)
**Trạng thái**: đã chốt qua `speckit-clarify`

Ghi lại câu trả lời ambiguity của Pha 2 (Quy tắc bắt buộc #2). Tham chiếu:
`specs/004-auth-accounts-history/spec.md`.

## D1 — Auth: **Supabase Auth** (không tự xây)
- **Chọn**: Dùng Supabase Auth (GoTrue) cho đăng ký/đăng nhập/đăng xuất email+mật khẩu. Ứng dụng
  KHÔNG tự hash/lưu mật khẩu.
- **Lý do**: khớp kiến trúc sản phẩm đã định (Supabase = pgvector + Auth + lịch sử, kho thống nhất);
  giảm bề mặt bảo mật tự viết. Constitution V.
- **Loại bỏ**: custom auth trên Postgres (tự hash/JWT) — nhiều rủi ro bảo mật tự lo hơn.

## D2 — Môi trường: **Supabase local stack (CLI)**, KHÔNG cloud ở Pha 2
- **Chọn**: `supabase init` + `supabase start` — chạy Postgres+pgvector + Auth + Studio **hoàn toàn
  local** (Docker), offline, **không cần tài khoản/project cloud**.
- **Lý do**: đưa Supabase Auth về sớm mà vẫn giữ tinh thần "chưa chạm cloud/secret thật" tới **Pha 6**.
  Không chạm hành động bị cấm (tạo tài khoản). Cùng engine nên tương thích cloud ở Pha 6.
- **⚠️ Đảo quyết định D5 của Pha 1** (feature #3 hoãn Supabase tới Pha 6): nay đưa **hạ tầng Supabase
  local** về Pha 2, nhưng **cloud thật** vẫn ở Pha 6. Ghi rõ để không nhầm.

## D3 — Kho dữ liệu: **Postgres của Supabase** làm kho thống nhất
- **Chọn**: chuyển `legal_chunks` (Pha 1) sang Postgres của Supabase local; thêm `public.search_history`.
  `DATABASE_URL` backend trỏ tới Postgres local của Supabase (mặc định cổng 54322).
- **Hệ quả với Pha 1**: `docker-compose` service `db` (pgvector thuần) được **thay** bằng Supabase stack;
  schema quản qua **Supabase migrations** (`supabase/migrations/*.sql`) thay cho `app/db/schema.sql` +
  `init_db.py` (giữ ingest/repository psycopg3 không đổi, chỉ đổi đích DB). Cần **re-ingest 293 chunk**.

## D4 — Phiên: **Supabase-managed + cookie httpOnly** (`@supabase/ssr`)
- **Chọn**: phiên do Supabase quản (`auth.sessions` + refresh token); `@supabase/ssr` lưu phiên trong
  **cookie httpOnly** (không lộ token cho JS), refresh ở middleware (server).
- **Lý do**: an toàn XSS (httpOnly), thu hồi được, chuẩn Next.js App Router. Đúng tinh thần câu trả lời
  clarify "session DB + cookie httpOnly".

## D5 — Lịch sử: **Supabase client + RLS**, FastAPI chỉ lo RAG
- **Chọn**: frontend đọc/ghi `search_history` trực tiếp qua Supabase client; **Row Level Security** với
  policy `user_id = auth.uid()` cô lập dữ liệu ở **tầng DB**. FastAPI `/api/query` **không** cần biết
  danh tính; ghi lịch sử là bước client-side sau khi có kết quả.
- **Lý do**: cô lập user mạnh nhất (RLS ở DB, Constitution V — SC-004) và idiomatic Supabase; backend
  gần như không đổi. Guest vẫn tra cứu (không ghi lịch sử).
- **Loại bỏ**: verify JWT ở FastAPI + psycopg3 cho history — thêm code, tự lo cô lập, kém an toàn hơn RLS.

## D6 — Phạm vi lịch sử: **tối thiểu**
- **Chọn**: mỗi bản ghi = `query + created_at + sources (jsonb các điều trích)`; **không** lưu toàn văn
  câu trả lời AI.
- **Lý do**: Constitution V (tối thiểu dữ liệu); câu trả lời tái tạo được.

## D7 — Guest: **tra cứu vẫn mở**
- Tài khoản là tuỳ chọn, chỉ THÊM lịch sử; người chưa đăng nhập tra cứu bình thường (giữ giá trị PoC cho
  người dân phổ thông).

## D8 — Đăng ký tiết lộ email đã tồn tại: CHẤP NHẬN ở Pha 2
- **Bối cảnh**: security-reviewer nêu (M-1) `signUp` trả "Email đã được đăng ký." → có thể dò tài khoản
  (account enumeration, OWASP A07).
- **Quyết định**: **giữ nguyên** ở Pha 2 — đúng spec US1 AC4 ("từ chối rõ ràng" khi email trùng); FR-010
  chỉ yêu cầu thông báo **chung** cho *đăng nhập* (đã làm đúng). UX đăng ký cần rõ ràng cho người dân phổ thông.
- **Pha 6**: khi bật `enable_confirmations = true`, chuyển sang thông báo trung tính
  ("Nếu email hợp lệ, bạn sẽ nhận email xác nhận") để khép lỗ dò tài khoản.

## Ngoài phạm vi Pha 2 (pha sau)
- Reset mật khẩu/xác minh email thật, OAuth/social (Supabase hỗ trợ, để sau).
- Rate-limit/security headers/CSP (Pha 4). Supabase **cloud** thật + deploy (Pha 6).

## Checklist bảo mật cho Pha 6 (từ security review — chưa làm ở Pha 2)
- [ ] Bật `enable_confirmations = true` (xác minh email) + đổi thông báo signUp sang trung tính (D8).
- [ ] Tăng `minimum_password_length` 6 → **8** (config.toml + validate `actions.ts`), theo NIST.
- [ ] Đưa mật khẩu DB ra `.env` (không in-line trong `docker-compose.yml`); dùng secret manager cho cloud.
- [ ] Application-level rate-limit cho `signIn`/`signUp` (Pha 4).
- [ ] Rà `service_role` chỉ ở server, không lộ client (đã đúng ở Pha 2 — giữ khi lên cloud).
