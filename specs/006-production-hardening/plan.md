# Implementation Plan: Production hardening

**Branch**: `006-production-hardening` | **Date**: 2026-07-04 | **Spec**: [spec.md](./spec.md)

## Summary

Thêm 3 lớp vận hành, không đổi hành vi RAG: (US1) **rate-limit** `/api/query` bằng slowapi in-memory;
(US2) **security headers + CSP static** ở frontend (next.config) + backend (middleware); (US3)
**observability đầy đủ** — OpenTelemetry auto-instrument + Prometheus `/metrics` + structured JSON log +
request-id. Exporter/collector thật để Pha 6.

## Technical Context

**Language/Version**: Python 3.12 (backend) · TypeScript/Next 16 (frontend).
**Primary Dependencies (thêm)**: backend `slowapi`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`,
`opentelemetry-exporter-otlp` (tùy chọn), `prometheus-fastapi-instrumentator`, `python-json-logger`.
**Testing**: pytest (TestClient — rate-limit 429, headers, /metrics, request-id, JSON log, no-PII) + Playwright
(security headers ở frontend).
**Constraints**: KHÔNG phá SSE streaming (rate-limit kiểm trước stream; middleware/OTel không buffer); KHÔNG
phá Supabase auth (CSP `connect-src`); không log secret/PII; RAG không đổi.
**Scale/Scope**: thêm `backend/app/observability/` + `middleware`; sửa `main.py`, `config.py`, `routers/query.py`,
`pyproject.toml`; frontend `next.config.ts`. Không đổi RAG/auth core.

## Constitution Check

| Nguyên tắc | Đánh giá | Trạng thái |
|-----------|----------|-----------|
| I. Chống bịa | RAG không đổi; verify 3 acceptance case + Điều 58 | ✅ PASS (gate) |
| II. Verbatim | Không đụng dữ liệu | ✅ PASS (N/A) |
| III. Test-First & ≥80% | TDD: test rate-limit/headers/metrics/log viết trước | ✅ PASS (gate) |
| IV. Minh bạch | UI không đổi; thêm X-Request-ID để đối chiếu | ✅ PASS |
| V. Riêng tư/secret | Log KHÔNG secret/PII (không log toàn văn câu hỏi/email); rà soát | ✅ PASS (gate) |
| VI. Đơn giản | Dùng lib chuẩn (slowapi/OTel/prometheus) thay vì tự viết; middleware nhỏ | ✅ PASS |

## Project Structure

```text
backend/
├── app/
│   ├── config.py                 # (sửa) +rate_limit, +log_level, +service_name (OTel)
│   ├── observability/            # (mới)
│   │   ├── __init__.py
│   │   ├── logging_config.py     # JSON formatter + configure_logging(); request_id contextvar
│   │   ├── middleware.py         # RequestContextMiddleware (request-id + timing + structured log)
│   │   ├── security.py           # SecurityHeadersMiddleware (nosniff, frame, referrer, permissions, CSP)
│   │   ├── ratelimit.py          # Limiter (slowapi) + 429 handler; limit đọc từ settings (callable)
│   │   └── otel.py               # setup_otel(app) (instrument FastAPI, exporter theo env, no-op mặc định)
│   ├── routers/query.py          # (sửa) thêm request: Request + @limiter.limit(...)
│   └── main.py                   # (sửa) configure_logging + middleware + rate-limit + OTel + /metrics
└── tests/
    ├── test_ratelimit.py         # (mới) 429 khi vượt; /health & /metrics không bị limit
    ├── test_security_headers.py  # (mới) headers + CSP có mặt; SSE vẫn chạy
    └── test_observability.py     # (mới) X-Request-ID; JSON log có trường; /metrics Prometheus; no-PII

frontend/
└── next.config.ts                # (sửa) async headers(): security headers + CSP static (connect-src Supabase)
```

**Structure Decision**: Gom lớp vận hành vào `app/observability/`. Thứ tự middleware trong `main.py`
quan trọng: SecurityHeaders + RequestContext bọc ngoài; OTel instrument app; rate-limit qua slowapi
(app.state.limiter + handler); Prometheus instrumentator expose `/metrics`. `routers/query.py` chỉ thêm
decorator limit (cần `request: Request`). RAG/service không đụng.

## Ghi chú then chốt
- **SSE-safe**: rate-limit kiểm ở tầng decorator (trước khi `search_stream` chạy). Middleware headers set
  trên response trước khi body stream — không buffer generator.
- **CSP connect-src**: lấy `NEXT_PUBLIC_SUPABASE_URL` lúc build config để cho phép auth; kèm backend origin.
- **OTel no-op ở dev**: nếu không có `OTEL_EXPORTER_OTLP_ENDPOINT` → dùng exporter console/không xuất, app
  vẫn chạy. Không phá SSE (instrumentation FastAPI xử lý streaming).
- **Không PII**: log độ dài câu hỏi (len) thay vì toàn văn; không log email/khoá.

## Complexity Tracking
> Không vi phạm — dùng thư viện chuẩn cho từng mối quan tâm; mỗi middleware nhỏ, tách file.
