# Tasks: Production hardening

**Feature**: `006-production-hardening` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Tests**: BẮT BUỘC (Constitution III). Test viết trước implementation.

---

## Phase 1: Setup
- [ ] T001 `backend/pyproject.toml`: thêm `slowapi`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`,
  `opentelemetry-exporter-otlp-proto-http`, `prometheus-fastapi-instrumentator`, `python-json-logger`; `uv sync`
- [ ] T002 `backend/app/config.py`: thêm `rate_limit` (default "30/minute"), `log_level` ("INFO"),
  `service_name` ("vn-legal-backend"); env prefix VN_LEGAL_
- [ ] T003 [P] `backend/app/observability/__init__.py`

## Phase 2: US1 — Rate-limit (P1) 🎯 MVP

### Tests (viết trước)
- [ ] T004 [P] [US1] `tests/test_ratelimit.py`: đặt limit thấp → gọi `/api/query` vượt ngưỡng trả **429**;
  dưới ngưỡng SSE 200; `/health` gọi nhiều lần KHÔNG 429

### Implementation
- [ ] T005 [US1] `app/observability/ratelimit.py`: `Limiter` (key theo IP) + handler 429 (thông báo rõ,
  không lộ nội bộ); limit đọc từ `settings.rate_limit` (callable để test override được)
- [ ] T006 [US1] `routers/query.py`: thêm `request: Request` + `@limiter.limit(...)`; giữ nguyên StreamingResponse
- [ ] T007 [US1] `main.py`: gắn `app.state.limiter` + exception handler; loại trừ `/health`, `/metrics`

## Phase 3: US2 — Security headers + CSP (P2)

### Tests (viết trước)
- [ ] T008 [P] [US2] `tests/test_security_headers.py`: response backend có `X-Content-Type-Options: nosniff`,
  `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`; SSE `/api/query` vẫn 200 + streaming

### Implementation
- [ ] T009 [US2] `app/observability/security.py`: `SecurityHeadersMiddleware` thêm header cho mọi response
  (nosniff, DENY, referrer, permissions; HSTS chỉ khi production); không buffer SSE
- [ ] T010 [US2] `main.py`: `app.add_middleware(SecurityHeadersMiddleware)`
- [ ] T011 [US2] `frontend/next.config.ts`: `async headers()` — security headers + **CSP static**
  (`default-src 'self'`; `connect-src 'self' <NEXT_PUBLIC_SUPABASE_URL>`; `style-src 'self' 'unsafe-inline'`;
  `img-src 'self' data:`; `frame-ancestors 'none'`; `object-src 'none'`; `base-uri 'self'`)
- [ ] T012 [US2] Verify thủ công: `npm run build` + tải trang, không lỗi CSP; auth + tra cứu chạy

## Phase 4: US3 — Observability (P3)

### Tests (viết trước)
- [ ] T013 [P] [US3] `tests/test_observability.py`: response có header `X-Request-ID`; `/metrics` trả định
  dạng Prometheus + KHÔNG bị rate-limit; log 1 request là JSON có `request_id/method/path/status/duration_ms`;
  **KHÔNG** có toàn văn câu hỏi/secret trong log (no-PII)

### Implementation
- [ ] T014 [US3] `app/observability/logging_config.py`: JSON formatter + `configure_logging()`;
  `request_id` contextvar; helper log request (len câu hỏi thay vì toàn văn — no-PII)
- [ ] T015 [US3] `app/observability/middleware.py`: `RequestContextMiddleware` — sinh/nhận `X-Request-ID`,
  đo `duration_ms`, phát 1 bản ghi structured log/ request, trả header `X-Request-ID`
- [ ] T016 [US3] `app/observability/otel.py`: `setup_otel(app)` — `FastAPIInstrumentor.instrument_app`,
  exporter theo env (`OTEL_EXPORTER_OTLP_ENDPOINT`), no-op/console mặc định; tương quan trace_id vào log
- [ ] T017 [US3] `main.py`: `configure_logging()`, add `RequestContextMiddleware`, `setup_otel(app)`,
  `Instrumentator().instrument(app).expose(app)` (endpoint `/metrics`)

## Phase 5: Verify & Polish
- [ ] T018 3 acceptance case gốc + guarantee Điều 58 (không hồi quy); SSE end-to-end còn chạy
- [ ] T019 [P] `docs/architecture.md`: thêm mục "Vận hành" (rate-limit, security headers/CSP, OTel/metrics)
- [ ] T020 [P] `backend/.env.example` + `frontend/.env.local.example`: thêm biến (rate_limit, log_level, OTEL_*)
- [ ] T021 `uv run pytest --cov=app` ≥80% + `ruff check` sạch; `npm run build` + Playwright headers (nếu có)

---

## Dependencies
```
Setup (T001–T003) → US1 (T004–T007) → US2 (T008–T012) → US3 (T013–T017) → Verify (T018–T021)
```
US1/US2/US3 độc lập tương đối; làm tuần tự cho gọn. RAG core không đụng → test cũ giữ xanh.

## MVP
US1 (rate-limit, T001–T007) = bảo vệ endpoint đắt nhất. US2/US3 là tăng cường.
