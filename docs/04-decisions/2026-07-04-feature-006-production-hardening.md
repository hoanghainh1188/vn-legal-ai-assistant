# Quyết định — Feature #6 (Pha 4): Production hardening

**Ngày**: 2026-07-04
**Feature**: `006-production-hardening` (issue #6, roadmap epic #2 — Pha 4)

## D1 — Rate-limit: **slowapi (in-memory)**
- **Chọn**: `slowapi` (dựa trên `limits`) cho FastAPI — `Limiter` theo IP, decorator trên `/api/query`,
  handler trả **429**. Lưu **in-memory** (đơn-instance).
- **Kiểm ngưỡng TRƯỚC khi stream** (SSE-safe): slowapi chạy ở tầng request trước khi trả StreamingResponse.
- **Cấu hình**: ngưỡng + cửa sổ qua env (`VN_LEGAL_RATE_LIMIT`, vd "30/minute").
- **Loại bỏ**: tự viết middleware (phải tự lo cửa sổ trượt/dọn bộ nhớ). **Redis** đa-instance → Pha 6.
- `/health`, `/metrics` **miễn** rate-limit.

## D2 — Security headers + CSP: **pragmatic static**
- **Headers** (frontend qua `next.config.ts` + backend qua middleware): `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY` (+ CSP `frame-ancestors 'none'`), `Referrer-Policy: strict-origin-when-cross-origin`,
  `Permissions-Policy` (camera/mic/geo = ()), `Strict-Transport-Security` (chỉ bật khi production/HTTPS — Pha 6).
- **CSP static** (không nonce ở Pha 4): `default-src 'self'`; `connect-src 'self' <SUPABASE_URL>` (auth) +
  backend; `img-src 'self' data:`; `style-src 'self' 'unsafe-inline'` (Next/Tailwind cần); `script-src 'self'`
  (+ `'unsafe-inline'` nếu Next runtime yêu cầu — xác minh khi implement); `object-src 'none'`; `base-uri 'self'`.
- **Lý do**: ít rủi ro chặn nhầm app/auth/SSE; đủ giảm bề mặt tấn công. **Siết nonce-based** (theo rule bảo
  mật web) để **Pha 6** khi deploy HTTPS thật + đã ổn định layout.
- **Loại bỏ**: nonce-based per-request ngay ở Pha 4 — phức tạp với Next 16 + Supabase + Tailwind, dễ vỡ.

## D3 — Observability: **đầy đủ (OpenTelemetry + Prometheus)**
- **Traces**: `opentelemetry-instrumentation-fastapi` auto-instrument HTTP request. Exporter cấu hình qua env
  chuẩn OTel; **mặc định console/no-op ở dev** (chạy được KHÔNG cần collector). Không phá SSE.
- **Metrics**: `prometheus-fastapi-instrumentator` phơi **`/metrics`** (request count, latency histogram,
  in-progress) — sẵn sàng để Prometheus scrape ở Pha 6.
- **Logs**: structured **JSON** (stdlib logging + formatter), mỗi request 1 bản ghi (request_id, method, path,
  status, duration_ms), **tương quan trace_id**. KHÔNG log secret/PII (không log toàn văn câu hỏi/email).
- **Request ID**: middleware tạo/nhận `X-Request-ID`, gắn log + trả header.
- **Lý do**: người dùng chọn mức đầy đủ; instrument sẵn để khi có hạ tầng quan sát (Pha 6) chỉ cần trỏ OTLP
  endpoint + Prometheus scrape, không phải sửa code.
- **Ngoài phạm vi Pha 4**: dựng Jaeger/Prometheus/Grafana thật, dashboard, alerting → **Pha 6** (hạ tầng).

## D4 — Ràng buộc chung
- Không phá **SSE streaming** (rate-limit trước stream; OTel/headers không buffer).
- Không phá **Supabase auth** (CSP `connect-src` cho Supabase URL).
- Không đổi hành vi RAG (3 acceptance case + Điều 58).
- HSTS + đọc `X-Forwarded-For` (IP thật sau reverse proxy) cấu hình ở **Pha 6**.

## Checklist bảo mật cho Pha 6 (từ review Pha 4 — cố ý hoãn)
- [ ] **CSP nonce-based**: bỏ `'unsafe-inline'` trong `script-src` production (H1) — thay bằng nonce per-request;
  thêm CI check khẳng định `unsafe-inline` vắng mặt trong CSP build production.
- [ ] **Rate-limit IP thật**: sau reverse proxy, `get_remote_address` chỉ thấy IP proxy → mọi user chung 1 bucket.
  Bật `uvicorn --proxy-headers` + `ProxyHeadersMiddleware` (trusted hosts), đổi `key_func=get_ipaddr` (M1).
- [ ] **`/metrics` không public**: giới hạn mạng nội bộ (Nginx allowlist) hoặc token — tránh lộ path/latency (M4).
- [ ] Bật HSTS (`VN_LEGAL_ENVIRONMENT=production`) khi có HTTPS thật; thêm collector OTLP + Prometheus scrape.

## Đã xử lý ngay ở Pha 4 (từ review)
- Log lỗi chat provider: chỉ log loại + thông điệp cắt ngắn (không traceback đầy đủ) → tránh lọt query/PII.
- `X-Request-ID` client: validate định dạng + cắt ≤64 ký tự (chống log bloat/reflection).
- `trace_id` gắn vào structured log (tương quan log↔trace — FR-014).
- 429 kèm `Retry-After`; security headers ép cứng (không setdefault); HSTS so khớp không phân biệt hoa/thường;
  CORS `allow_headers` liệt kê cụ thể; pin `python-json-logger>=3.0`.
