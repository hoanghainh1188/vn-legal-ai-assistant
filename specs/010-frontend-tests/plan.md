# Implementation Plan: Frontend tests + E2E (Pha 5)

**Branch**: `010-frontend-tests` | **Date**: 2026-07-05 | **Spec**: [spec.md](./spec.md)

## Summary

Thêm **Vitest + RTL** cho unit test (`lib`, `hooks`, logic component) và **1 E2E Playwright mock-SSE** cho
luồng tra cứu. Tách rõ: `*.test.tsx` = Vitest, `*.spec.ts` = Playwright (e2e). Coverage ≥80% lib/hooks/logic.
Không đụng code app (chỉ test + cấu hình); tích hợp CI (bước `npm test`).

## Technical Context

**Language**: TypeScript / Next 16 / React.
**Testing**: Vitest (jsdom, coverage v8) + @testing-library/react + user-event + jest-dom; Playwright (mock SSE).
**Constraints**: unit KHÔNG chạm mạng/Supabase (mock `fetch` + supabase client); E2E deterministic (không
`waitForTimeout`); không flaky. Next 16 breaking → test tầng lib/hooks/logic.
**Scope**: config (vitest.config, setup, scripts) + 5 file unit test + 1 file e2e + CI.

## Constitution Check

| Nguyên tắc | Đánh giá | Trạng thái |
|-----------|----------|-----------|
| I. Chống bịa | Không đụng RAG/prompt | ✅ PASS (N/A) |
| II. Verbatim | Không đụng dữ liệu | ✅ PASS (N/A) |
| III. Test-First & ≥80% | Chính là feature test; coverage ≥80% lib/hooks/logic | ✅ PASS (gate) |
| IV. Minh bạch | Test làm rõ hành vi hiển thị nguồn/cảnh báo/lọc | ✅ PASS |
| V. Riêng tư | Mock supabase; không dữ liệu thật | ✅ PASS |
| VI. Đơn giản | 1 runner + mock; 0 abstraction app mới | ✅ PASS |

## Project Structure

```text
frontend/
├── vitest.config.ts            # (mới) jsdom, alias @, include *.test, exclude tests/e2e, coverage v8
├── vitest.setup.ts             # (mới) import @testing-library/jest-dom
├── package.json                # +scripts test/test:coverage; +devDeps vitest/RTL/jsdom
├── lib/
│   ├── api.test.ts             # (mới) searchStream SSE
│   └── history.test.ts         # (mới) saveHistory guest/insert (mock supabase)
├── hooks/
│   └── useStreamQuery.test.tsx # (mới) state machine (mock searchStream + saveHistory)
├── components/
│   ├── result/LegalReference.test.tsx  # (mới) formatDate/docLabel/isAmended/cảnh báo/rỗng
│   └── search/DomainFilter.test.tsx    # (mới) loading→chip/rỗng→null/onChange (mock fetch)
└── tests/e2e/
    └── search.spec.ts          # (mới) mock /api/query + /api/domains → luồng tra cứu + từ chối + lọc
.github/workflows/*.yml         # +bước npm ci + npm test (frontend unit)
```

**Structure Decision**: `.test.tsx` (Vitest) tách khỏi `.spec.ts` (Playwright) qua `include`/`exclude` để
2 runner không giẫm nhau. Mock ở ranh giới ngoài (`fetch`, supabase client, `searchStream`) → unit thuần,
không dịch vụ ngoài. E2E mock tại tầng mạng (`page.route`) → deterministic.

## Ghi chú
- Alias `@/` cho Vitest: `resolve.alias` trong vitest.config (hoặc `vite-tsconfig-paths`).
- Coverage chỉ tính `lib/**`, `hooks/**`, `components/**` (bỏ config/e2e) để phản ánh logic thật.
- `useStreamQuery` test: mock `@/lib/api` (searchStream async generator) + `@/lib/history` (saveHistory).
- CI: unit test là bước bắt buộc; E2E search (mock) chạy được không cần Supabase, nhưng để đơn giản có thể
  giữ E2E ở job riêng/không chặn (ghi rõ). Ưu tiên gate = unit.

## Complexity Tracking
> Không vi phạm — chỉ thêm hạ tầng test, 0 abstraction app.
