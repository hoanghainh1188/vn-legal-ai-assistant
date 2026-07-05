# Tasks: Frontend tests + E2E (Pha 5)

**Feature**: `010-frontend-tests` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Cách làm**: cài runner trước (T001-T003), rồi viết test (đỏ→xanh vì code đã tồn tại → test bám hành vi
thật), coverage ≥80%.

---

## Phase 1: Hạ tầng Vitest
- [ ] T001 Cài devDeps: `vitest @vitejs/plugin-react @testing-library/react @testing-library/user-event
  @testing-library/jest-dom jsdom @vitest/coverage-v8`
- [ ] T002 `vitest.config.ts`: env jsdom, alias `@`, `include: ['**/*.test.{ts,tsx}']`,
  `exclude: [tests/e2e, node_modules, .next]`, coverage v8 (include lib/hooks/components), setup file
- [ ] T003 `vitest.setup.ts` (import jest-dom); `package.json` scripts `test`, `test:coverage`

## Phase 2: Unit test — lib (US1)
- [ ] T004 [P] `lib/api.test.ts`: `searchStream` — yield sources/token/done đúng thứ tự; **ghép buffer** khi
  chunk cắt giữa dòng; **bỏ dòng JSON hỏng**; ném lỗi khi `!response.ok`; ném lỗi khi không có body;
  body chứa `domain` đã chọn (mock `fetch` + ReadableStream)
- [ ] T005 [P] `lib/history.test.ts`: guest (getUser→null) → KHÔNG insert; đã đăng nhập → insert với
  refs map từ sources (mock `@/lib/supabase/client`)

## Phase 3: Unit test — hook + component (US1)
- [ ] T006 [P] `hooks/useStreamQuery.test.tsx`: idle ban đầu; loading khi search; `sources`→streaming;
  `token` cộng dồn answer; `done`→status done + gọi `saveHistory`; `error` giữa chừng→status error;
  `reset`→idle (mock `@/lib/api`, `@/lib/history`)
- [ ] T007 [P] `components/result/LegalReference.test.tsx`: rỗng→null; docLabel Luật/NĐ/TT đúng;
  badge + **cảnh báo gộp** khi có "hết hiệu lực"; formatDate "2024-08-01"→"01/08/2024"; hiện lĩnh vực
- [ ] T008 [P] `components/search/DomainFilter.test.tsx`: loading (skeleton) trước fetch; sau fetch hiện
  "Tất cả" + lĩnh vực; rỗng→null; click chip gọi `onChange` đúng giá trị (mock `fetch`)

## Phase 4: E2E luồng tra cứu (US2)
- [ ] T009 `tests/e2e/search.spec.ts`: `page.route` mock `/api/domains` + `/api/query` (SSE cố định) →
  (a) hỏi → hiện "Cơ sở pháp lý" + câu trả lời; (b) ca từ chối → hiện câu từ chối; (c) bộ lọc lĩnh vực hiển thị

## Phase 5: CI + chốt
- [ ] T010 CI workflow: thêm bước `npm ci` + `npm test` (frontend unit) — không cần service
- [ ] T011 Chạy `npm run test:coverage` ≥80% (lib/hooks/components-logic); `npx tsc --noEmit`; e2e auth/history
  không hồi quy (chạy khi có Supabase)
- [ ] T012 [P] `docs/architecture.md` (mục testing) + README (cách chạy test)

---

## Dependencies
```
T001-T003 (hạ tầng) → T004-T008 (unit) ∥ T009 (e2e) → T010-T012 (CI + chốt)
```

## MVP
US1 (unit lib/hooks/component ≥80%) = giá trị cốt lõi; US2 (E2E mock) hoàn thiện luồng.
