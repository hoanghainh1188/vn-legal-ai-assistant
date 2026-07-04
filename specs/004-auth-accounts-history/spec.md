# Feature Specification: Tài khoản + Đăng nhập + Lịch sử tra cứu

**Feature Branch**: `004-auth-accounts-history`

**Created**: 2026-07-04

**Status**: Draft

**Input**: Issue #4 — thêm tài khoản người dùng + lưu lịch sử tra cứu trên nền Postgres (Pha 1),
thuộc roadmap epic #2 (Pha 2).

## Clarifications

### Session 2026-07-04

- Q: Cơ chế auth — custom trên Postgres hay Supabase Auth? → A: **Supabase Auth**, chạy **Supabase local
  stack (CLI)** — offline, không cần tài khoản cloud; đảo quyết định D5 của Pha 1 (đưa Supabase về sớm).
  Cloud thật vẫn để Pha 6.
- Q: Phiên đăng nhập — session DB (cookie httpOnly) hay JWT stateless? → A: **Phiên do Supabase quản lý**
  (`auth.sessions`) + **cookie httpOnly** qua `@supabase/ssr` (không lộ token cho JS, thu hồi được).
- Q: Lịch sử lưu gì? → A: **Tối thiểu** — câu hỏi + thời điểm + nguồn trích (document_id + số điều + tiêu đề);
  KHÔNG lưu toàn văn câu trả lời (Constitution V).
- Q: Tìm kiếm ẩn danh còn hoạt động không? → A: **Có** — tài khoản chỉ THÊM lịch sử, không chặn tra cứu.
- Q: Truy cập search_history qua đâu? → A: **Supabase client + RLS** (frontend đọc/ghi trực tiếp, cô lập
  user bằng Row Level Security `user_id = auth.uid()`); FastAPI chỉ lo RAG.
- Q: Kho dữ liệu? → A: **Postgres của Supabase** (local stack) làm kho thống nhất — chuyển `legal_chunks`
  (Pha 1) + `search_history` vào đây; schema quản qua **Supabase migrations**.

## User Scenarios & Testing *(mandatory)*

> Ghi chú: giá trị là cho phép người dân **quay lại xem các câu đã tra cứu** và cá nhân hoá.
> Tài khoản là **tuỳ chọn** — không được làm hỏng luồng tra cứu ẩn danh hiện có.

### User Story 1 - Đăng ký & đăng nhập (Priority: P1)

Người dùng tạo tài khoản bằng email + mật khẩu, đăng nhập, và đăng xuất. Sau đăng nhập, hệ
thống nhận diện được họ ở các lượt sau (phiên).

**Why this priority**: Đây là nền tảng — không có tài khoản thì không có lịch sử cá nhân. Cũng là
phần **nhạy cảm bảo mật** nhất (Constitution V), phải đúng trước tiên.

**Independent Test**: Đăng ký một tài khoản mới, đăng xuất, đăng nhập lại bằng đúng thông tin →
thành công; sai mật khẩu → bị từ chối; xem được thông tin tài khoản hiện tại khi đã đăng nhập.

**Acceptance Scenarios**:

1. **Given** email chưa tồn tại, **When** người dùng đăng ký với email + mật khẩu hợp lệ, **Then**
   tài khoản được tạo (mật khẩu **được hash**, không lưu plaintext) và họ ở trạng thái đăng nhập.
2. **Given** một tài khoản đã có, **When** đăng nhập đúng mật khẩu, **Then** hệ thống cấp phiên và
   nhận diện họ ở lượt sau; **When** sai mật khẩu, **Then** bị từ chối với thông báo chung (không
   tiết lộ email tồn tại hay không).
3. **Given** đang đăng nhập, **When** đăng xuất, **Then** phiên bị vô hiệu; truy cập tài nguyên cần
   auth sau đó bị từ chối.
4. **Given** email đã tồn tại, **When** đăng ký lại cùng email, **Then** bị từ chối rõ ràng.

---

### User Story 2 - Tự lưu lịch sử tra cứu (Priority: P2)

Khi người **đã đăng nhập** thực hiện một lượt tra cứu, hệ thống tự lưu lượt đó vào lịch sử của họ
(câu hỏi + thời điểm + nguồn trích dẫn). Người **chưa đăng nhập** vẫn tra cứu bình thường, chỉ
không lưu lịch sử.

**Why this priority**: Đây là giá trị chính của Pha 2. Phụ thuộc US1 (cần danh tính).

**Independent Test**: Đăng nhập, tra cứu vài câu → các lượt xuất hiện trong lịch sử; tra cứu khi
chưa đăng nhập → không tạo bản ghi lịch sử, nhưng câu trả lời vẫn trả về bình thường.

**Acceptance Scenarios**:

1. **Given** đang đăng nhập, **When** tra cứu một câu, **Then** một bản ghi lịch sử được tạo gắn với
   user đó (câu hỏi + thời điểm + nguồn trích).
2. **Given** chưa đăng nhập, **When** tra cứu, **Then** câu trả lời vẫn trả về đầy đủ (SSE không đổi)
   và **không** bản ghi lịch sử nào được tạo.
3. **Given** lượt tra cứu, **Then** việc lưu lịch sử **không** làm đổi nội dung/luồng câu trả lời
   (3 acceptance case gốc + guarantee Điều 58 giữ nguyên).

---

### User Story 3 - Xem lại lịch sử của mình (Priority: P3)

Người dùng đã đăng nhập xem danh sách các câu đã tra cứu của **chính mình**, mới nhất trước.

**Why this priority**: Hoàn thiện vòng giá trị (lưu → xem lại). Phụ thuộc US2.

**Independent Test**: Đăng nhập hai tài khoản khác nhau, mỗi tài khoản chỉ thấy lịch sử của mình.

**Acceptance Scenarios**:

1. **Given** đang đăng nhập và có lịch sử, **When** mở trang lịch sử, **Then** thấy các lượt của
   mình theo thứ tự thời gian giảm dần.
2. **Given** hai user A và B, **When** A xem lịch sử, **Then** A **không** thấy bất kỳ lượt nào của B
   (cô lập dữ liệu — Constitution V).

### Edge Cases

- Email sai định dạng / mật khẩu quá ngắn → từ chối với lỗi validation rõ ràng.
- Truy cập endpoint cần auth khi chưa đăng nhập / phiên hết hạn / phiên đã đăng xuất → 401 rõ ràng.
- Đăng nhập sai nhiều lần → thông báo chung, không tiết lộ email có tồn tại (chống dò tài khoản).
  (Rate-limit chi tiết thuộc Pha 4.)
- Secret (khoá ký phiên / DB) thiếu khi khởi động → fail-fast, không chạy với secret mặc định yếu.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI cho phép đăng ký bằng **email + mật khẩu** qua **Supabase Auth**; email
  duy nhất; mật khẩu do Supabase **hash** (ứng dụng KHÔNG bao giờ chạm plaintext, KHÔNG tự lưu mật khẩu).
- **FR-002**: Hệ thống PHẢI cho phép đăng nhập và **đăng xuất** (vô hiệu phiên) qua Supabase Auth.
- **FR-003**: Phiên PHẢI được lưu trong **cookie httpOnly** qua `@supabase/ssr` (không lộ token cho
  JavaScript); refresh phiên xử lý ở server (middleware).
- **FR-004**: Hệ thống PHẢI lấy được **người dùng hiện tại** (id + email) khi đã đăng nhập, và coi là
  ẩn danh khi chưa/đã hết phiên.
- **FR-005**: Khi người **đã đăng nhập** tra cứu, hệ thống PHẢI lưu một bản ghi `search_history` gắn với
  user (câu hỏi + thời điểm + nguồn trích) — ghi qua **Supabase client** (áp RLS).
- **FR-006**: Người **chưa đăng nhập** PHẢI vẫn tra cứu được bình thường; hợp đồng `/api/query` và luồng
  SSE **không đổi** về mặt câu trả lời (backend RAG **không** cần biết danh tính).
- **FR-007**: Người dùng PHẢI xem được lịch sử **của chính mình** (mới nhất trước); **cô lập** dữ liệu
  bằng **Row Level Security** (`user_id = auth.uid()`) — không ai đọc được lịch sử người khác kể cả khi
  gọi thẳng API dữ liệu.
- **FR-008**: Việc lưu lịch sử PHẢI **không** thay đổi nội dung/thứ tự câu trả lời hay hành vi retrieval
  (3 acceptance case gốc + guarantee Điều 58 giữ nguyên).
- **FR-009**: Mọi bí mật (khoá Supabase, thông tin DB) PHẢI lấy từ biến môi trường; KHÔNG hardcode;
  KHÔNG log. `service_role`/khoá nhạy cảm KHÔNG được lộ ra client (chỉ dùng `anon key` ở frontend).
- **FR-010**: Hệ thống PHẢI validate input ở biên (định dạng email, độ dài mật khẩu tối thiểu) và hiển
  thị lỗi rõ ràng; lỗi đăng nhập dùng thông báo chung (không tiết lộ email tồn tại hay không).
- **FR-011**: `search_history` (và `legal_chunks` của Pha 1) PHẢI nằm trong **Postgres của Supabase**
  (kho thống nhất); schema quản qua **Supabase migrations** (tạo lại được, idempotent).
- **FR-012**: Frontend PHẢI có giao diện **đăng ký / đăng nhập / đăng xuất** và **xem lịch sử**; trạng
  thái đăng nhập hiển thị (vd header). Người chưa đăng nhập vẫn dùng được trang tra cứu.

### Key Entities

- **User**: do **Supabase Auth** quản (`auth.users`: id uuid, email, mật khẩu đã hash…). Ứng dụng không
  tự tạo bảng users, chỉ tham chiếu `auth.users(id)`.
- **Session**: do **Supabase Auth** quản (`auth.sessions` + refresh token); phía app giữ trong cookie httpOnly.
- **SearchHistory** (`public.search_history`): `id, user_id (→ auth.users.id), query, created_at,
  sources (jsonb: [{document_id, article_number, article_title}])`. Có **RLS**: mỗi user chỉ thao tác
  hàng của `auth.uid()`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Người dùng đăng ký → đăng xuất → đăng nhập lại thành công; sai mật khẩu bị từ chối. 100%
  qua test tự động.
- **SC-002**: **0** mật khẩu plaintext trong DB/log; **0** bí mật hardcode; secret từ env (xác minh test + rà soát).
- **SC-003**: Người đã đăng nhập tra cứu → có bản ghi lịch sử; chưa đăng nhập → **0** bản ghi, câu trả
  lời vẫn đầy đủ.
- **SC-004**: **Cô lập dữ liệu**: user A không truy cập được lịch sử user B (test khẳng định).
- **SC-005**: 3 acceptance case gốc + guarantee Điều 58 vẫn xanh (không hồi quy RAG).
- **SC-006**: Độ phủ test ≥ **80%**, gồm test auth (đăng ký/đăng nhập/đăng xuất/guard) và cô lập lịch sử.

## Assumptions

- Dùng **Supabase local stack (CLI)** — Postgres+pgvector+Auth chạy offline qua Docker; **không** cần
  tài khoản/project cloud ở Pha 2. Supabase cloud thật để **Pha 6** (deploy).
- Kho dữ liệu chuyển sang **Postgres của Supabase**: `legal_chunks` (Pha 1) di trú vào đây; `DATABASE_URL`
  của backend trỏ tới Postgres local của Supabase; ingest/RAG hoạt động không đổi (chỉ đổi đích DB).
- Backend RAG **không** cần xác thực — lịch sử ghi client-side qua Supabase; `/api/query` giữ nguyên.
- **Reset mật khẩu qua email / xác minh email / OAuth**: Supabase hỗ trợ nhưng gửi email thật ngoài phạm
  vi Pha 2 (local dùng Inbucket nếu cần); giữ tối giản.
- Rate-limit/security headers/CSP chi tiết thuộc **Pha 4**.
- Không đổi hành vi RAG lõi (3 acceptance case + guarantee Điều 58).
