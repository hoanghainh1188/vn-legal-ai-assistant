# Quyết định — Feature #10 (Pha 5): Frontend tests + E2E

**Ngày**: 2026-07-05
**Feature**: `010-frontend-tests` (issue #10)

## D1 — Unit runner: **Vitest + React Testing Library**
- **Chọn**: Vitest (ESM/Vite-native, nhanh, TS sẵn, hợp React/Next) + `@testing-library/react` +
  `@testing-library/user-event` + `jsdom`. Script `npm test` / `npm run test:coverage` (provider `v8`).
- **Loại**: Jest (cấu hình ESM/Next nặng, chậm hơn).

## D2 — E2E luồng tra cứu: **mock SSE qua Playwright route**
- **Chọn**: `page.route("**/api/query", ...)` trả body `text/event-stream` cố định (sources/token/done, và
  ca từ chối) → test **deterministic**, nhanh, không cần Ollama/backend. Cũng mock `/api/domains` cho bộ lọc.
- **Loại**: chạy backend+Ollama thật (chậm, flaky, khó CI). Có thể thêm 1 E2E "smoke thật" opt-in sau.
- Giữ E2E auth+history (Pha 2) — không hồi quy.

## D3 — Phạm vi: **unit + E2E chức năng**; visual/a11y để sau
- Pha 5 = unit (lib/hooks/component-logic) + E2E chức năng (mock). Visual regression baseline + a11y
  automation (@axe-core) + cross-browser matrix + Lighthouse → **để pha sau** (giữ Pha 5 gọn, ship nhanh).

## Bề mặt test (đã khảo sát)
| Đơn vị | Test gì |
|--------|---------|
| `lib/api.searchStream` | thứ tự event, ghép buffer chunk-boundary, bỏ dòng JSON hỏng, lỗi HTTP/no-body, gửi `domain` |
| `hooks/useStreamQuery` | idle→loading→streaming→done; cộng dồn token; `error` giữa chừng; gọi `saveHistory` khi done; `reset` |
| `lib/history.saveHistory` | guest (no user) → không insert; đã đăng nhập → map sources→refs + insert |
| `components` | `LegalReference` (formatDate/docLabel/isAmended/cảnh báo gộp/rỗng→null); `DomainFilter` (loading→chip/rỗng→null/onChange) |

## Lưu ý
- Next 16 breaking (AGENTS.md) → test tầng lib/hooks/logic, tránh phụ thuộc nội bộ Next runtime.
- Unit test mock `fetch` (api) + supabase client (history) → không chạm mạng/DB thật.
- CI: thêm bước `npm test` (unit, không cần service). E2E ghi rõ phụ thuộc (Supabase cho auth/history; mock cho search).
