# Feature Specification: Production hardening — rate-limit, security headers/CSP, observability

**Feature Branch**: `006-production-hardening`

**Created**: 2026-07-04

**Status**: Draft

**Input**: Issue #6 — chuẩn bị vận hành an toàn trước deploy (roadmap epic #2, Pha 4).

## Clarifications

### Session 2026-07-04

- Q: Rate-limit backend dùng gì? → A: **slowapi** (in-memory) — decorator + 429 handler; Redis đa-instance để Pha 6.
- Q: CSP mức nào? → A: **Pragmatic (static CSP)** — directive hợp lý cho Next/Supabase/Tailwind, ít rủi ro
  chặn nhầm; siết nonce-based ở Pha 6 khi deploy HTTPS thật.
- Q: Độ sâu observability? → A: **Đầy đủ (metrics/OTel)** — OpenTelemetry auto-instrument FastAPI (traces) +
  Prometheus `/metrics` + structured JSON log tương quan trace-id + request-id. Exporter cấu hình qua env
  (`OTEL_*`), mặc định console/no-op ở dev (chạy không cần collector). Backend quan sát thật (Jaeger/
  Prometheus/Grafana) là hạ tầng **Pha 6**.

## User Scenarios & Testing *(mandatory)*

> "Người dùng" là **đội vận hành** + sản phẩm nói chung: chống lạm dụng, giảm bề mặt tấn công web,
> và có khả năng quan sát/audit. Người dân tra cứu KHÔNG được cảm nhận thay đổi (trừ khi lạm dụng).

### User Story 1 - Chống lạm dụng endpoint tra cứu (Priority: P1)

Endpoint `/api/query` (tốn kém: embedding + LLM) bị giới hạn tần suất theo IP; ai gọi quá mức nhận
lỗi rõ ràng (429), người dùng bình thường không bị ảnh hưởng.

**Why this priority**: Endpoint đắt nhất, dễ bị lạm dụng/DoS. Bảo vệ chi phí + tính sẵn sàng.

**Independent Test**: Gọi `/api/query` vượt ngưỡng trong cửa sổ thời gian → nhận **429**; dưới ngưỡng
→ hoạt động bình thường (SSE streaming không bị phá).

**Acceptance Scenarios**:

1. **Given** ngưỡng rate-limit, **When** một IP gọi vượt ngưỡng trong cửa sổ, **Then** trả **429** với
   thông báo rõ ràng, KHÔNG lộ chi tiết nội bộ.
2. **Given** dưới ngưỡng, **When** người dùng tra cứu, **Then** SSE stream (sources/token/done) hoạt động
   **y như cũ**.
3. **Given** endpoint `/health`, **When** gọi nhiều lần, **Then** KHÔNG bị rate-limit (để giám sát).

---

### User Story 2 - Giảm bề mặt tấn công web (security headers + CSP) (Priority: P2)

Phản hồi HTTP kèm các security header chuẩn và **Content-Security-Policy**; frontend không bị clickjack,
MIME-sniff, rò rỉ referrer; script/style bị giới hạn nguồn.

**Why this priority**: Phòng thủ chiều sâu chống XSS/clickjacking. P2 vì phụ thuộc app đã chạy ổn (P1).

**Independent Test**: Tải trang chính + gọi API → kiểm tra response có `X-Content-Type-Options: nosniff`,
`X-Frame-Options`/`frame-ancestors`, `Referrer-Policy`, `Permissions-Policy`, và `Content-Security-Policy`;
app + auth Supabase + SSE vẫn hoạt động (CSP không chặn nhầm).

**Acceptance Scenarios**:

1. **Given** frontend, **When** tải trang, **Then** response có đủ security headers + CSP; trang render
   bình thường (không lỗi CSP chặn script/style hợp lệ).
2. **Given** CSP, **When** app gọi Supabase (`NEXT_PUBLIC_SUPABASE_URL`) và backend, **Then** `connect-src`
   cho phép các origin đó; auth + tra cứu không bị chặn.
3. **Given** backend API, **When** trả response, **Then** có `X-Content-Type-Options: nosniff` + header an toàn.

---

### User Story 3 - Quan sát & audit vận hành (observability) (Priority: P3)

Mỗi request backend có **request ID** + log có cấu trúc (method, path, status, thời gian xử lý); log
KHÔNG chứa secret/PII. Đủ để lần vết sự cố và audit.

**Why this priority**: Hỗ trợ vận hành/điều tra; lợi ích dài hạn, không chặn giá trị trước mắt.

**Independent Test**: Gọi API → log phát ra bản ghi có cấu trúc gồm request_id + đường dẫn + status +
thời gian; response có header `X-Request-ID`; kiểm tra không có secret trong log.

**Acceptance Scenarios**:

1. **Given** một request, **When** xử lý xong, **Then** có 1 bản ghi log cấu trúc: request_id, method, path,
   status_code, duration_ms.
2. **Given** log, **When** rà soát, **Then** KHÔNG có connection string/khoá/PII (Constitution V).
3. **Given** response, **When** client nhận, **Then** có header `X-Request-ID` để đối chiếu khi báo lỗi.

### Edge Cases

- Rate-limit không được **đệm** (buffer) SSE — phải kiểm ngưỡng TRƯỚC khi bắt đầu stream.
- CSP không được chặn: Next.js runtime, Supabase Auth (`connect-src`), font/style hợp lệ, react-markdown.
- Rate-limit theo IP sau reverse proxy (Pha 6) cần đọc `X-Forwarded-For` đúng — ghi nhận, cấu hình ở deploy.
- Log lỗi phải giữ nguyên hành vi SSE `error` (FR-011 cũ) — không nuốt lỗi, không lộ chi tiết nhạy cảm cho client.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI giới hạn tần suất `/api/query` theo IP (ngưỡng + cửa sổ **cấu hình được** qua
  env); vượt → **429** với thông báo rõ ràng, không lộ nội bộ.
- **FR-002**: Rate-limit PHẢI kiểm TRƯỚC khi bắt đầu SSE stream; luồng streaming dưới ngưỡng **không đổi**.
- **FR-003**: `/health` (và endpoint giám sát) PHẢI **không** bị rate-limit.
- **FR-004**: Phản hồi frontend PHẢI kèm: `X-Content-Type-Options: nosniff`, chống clickjack
  (`X-Frame-Options`/CSP `frame-ancestors`), `Referrer-Policy`, `Permissions-Policy`, và **CSP**.
- **FR-005**: CSP PHẢI cho phép các nguồn hợp lệ của app (Next.js, Supabase URL, backend API, font/style)
  để auth + tra cứu + SSE **không bị chặn**.
- **FR-006**: Phản hồi backend PHẢI kèm `X-Content-Type-Options: nosniff` và header an toàn phù hợp; áp
  cho cả API thường và SSE mà **không phá** streaming.
- **FR-007**: `Strict-Transport-Security` PHẢI được cấu hình cho **production** (bật khi chạy HTTPS thật ở
  Pha 6); ở dev không bắt buộc.
- **FR-008**: Mỗi request backend PHẢI có **request ID** (tạo mới nếu client không gửi), gắn vào log và
  trả lại qua header `X-Request-ID`.
- **FR-009**: Backend PHẢI log **có cấu trúc** mỗi request: request_id, method, path, status_code,
  duration_ms; cấu hình mức log qua env.
- **FR-010**: Log PHẢI **không** chứa secret (connection string, khoá) hay PII (nội dung câu hỏi đầy đủ,
  email); Constitution V.
- **FR-011**: Hành vi RAG lõi (retrieval, prompt, SSE sources/token/done/error) PHẢI **không đổi**;
  3 acceptance case gốc + guarantee Điều 58 giữ nguyên.
- **FR-012**: Backend PHẢI được **auto-instrument OpenTelemetry** (traces cho HTTP request); exporter cấu
  hình qua env chuẩn (`OTEL_EXPORTER_OTLP_ENDPOINT`...), mặc định **console/no-op** ở dev (không cần collector).
  Instrument KHÔNG được phá SSE streaming.
- **FR-013**: Backend PHẢI phơi **`/metrics`** dạng Prometheus (request count, latency, in-progress) để scrape;
  `/metrics` KHÔNG bị rate-limit và KHÔNG chứa PII.
- **FR-014**: Log PHẢI tương quan được với trace (kèm `trace_id`/`request_id`) để lần vết một request xuyên
  suốt log ↔ trace.

### Key Entities

- **RateLimit config**: ngưỡng (số request) + cửa sổ (thời gian) + phạm vi (theo IP) — đọc từ env.
- **Security headers policy**: tập header + CSP directives áp cho frontend/backend.
- **Request log record**: request_id, method, path, status_code, duration_ms (không PII/secret).

## Success Criteria *(mandatory)*

- **SC-001**: Gọi `/api/query` vượt ngưỡng → **429** (test tự động); dưới ngưỡng SSE hoạt động như cũ.
- **SC-002**: Response frontend + backend có đủ security header + CSP (test kiểm header); app/auth/SSE không hỏng.
- **SC-003**: Mỗi request có `X-Request-ID` + 1 bản ghi log cấu trúc; **0** secret/PII trong log (rà soát + test).
- **SC-004**: 3 acceptance case gốc + guarantee Điều 58 vẫn xanh (không hồi quy).
- **SC-005**: Coverage backend ≥ **80%**; `/health` + `/metrics` không bị rate-limit (test).
- **SC-006**: `/metrics` trả định dạng Prometheus; app khởi động có OTel instrument (traces) mà SSE vẫn chạy.

## Assumptions

- **Ngoài phạm vi (Pha 6/sau)**: rate-limit lưu trữ **Redis** đa-instance; APM/OpenTelemetry/metrics đầy đủ;
  WAF; enforcement HSTS + đọc `X-Forwarded-For` trên hạ tầng thật (cấu hình lúc deploy).
- Dev chạy đơn-instance → rate-limit **in-memory** đủ ở Pha 4.
- Không đổi kiến trúc RAG/auth; chỉ thêm lớp middleware/headers/logging.
