# Feature Specification: Frontend tests + E2E (Pha 5)

**Feature Branch**: `010-frontend-tests`

**Created**: 2026-07-05

**Status**: Draft

**Input**: Issue #10 — bổ sung tầng test frontend. Hiện có Playwright E2E auth+history (Pha 2), chưa có
unit test.

## Clarifications

### Session 2026-07-05

- Q: Unit test runner? → A: **Vitest + React Testing Library** (nhanh, ESM/Vite-native, TS sẵn).
- Q: Chiến lược E2E luồng tra cứu? → A: **Mock SSE qua Playwright route** — chặn `/api/query` trả stream
  giả cố định → deterministic, nhanh, không cần Ollama/backend.
- Q: Phạm vi visual regression + a11y? → A: **Tập trung unit + E2E chức năng**; visual/a11y để pha sau.

## User Scenarios & Testing *(mandatory)*

> Giá trị: bắt hồi quy sớm cho logic frontend cốt lõi (parse stream, state machine, hiển thị nguồn/cảnh
> báo/lọc) mà không cần dựng cả backend+Ollama mỗi lần.

### User Story 1 - Unit test cho logic cốt lõi (Priority: P1)

Có test đơn vị cho `lib/api` (parse SSE), `useStreamQuery` (state machine), `lib/history` (guest skip),
và logic component (LegalReference/DomainFilter). Chạy nhanh, không cần backend.

**Independent Test**: `npm test` xanh; coverage ≥80% trên lib/hooks/component-logic.

**Acceptance Scenarios**:

1. **Given** SSE trả sources+token+done, **When** `searchStream` parse, **Then** yield đúng thứ tự event;
   bỏ qua dòng hỏng; ném lỗi khi HTTP !ok / không có body.
2. **Given** stream có `error` giữa chừng, **When** `useStreamQuery`, **Then** status="error", KHÔNG coi
   phần đã nhận là câu trả lời hoàn chỉnh.
3. **Given** chưa đăng nhập, **When** `saveHistory`, **Then** KHÔNG insert (guest skip).
4. **Given** nguồn có văn bản "hết hiệu lực", **When** render `LegalReference`, **Then** hiện cảnh báo gộp
   + badge; docLabel đúng loại (Luật/NĐ/TT); formatDate dạng VN.

### User Story 2 - E2E luồng tra cứu cốt lõi (Priority: P1)

Người dùng hỏi → thấy "Cơ sở pháp lý" + câu trả lời stream dần; câu ngoài phạm vi → hiển thị từ chối; chọn
bộ lọc lĩnh vực. E2E chạy **deterministic** (không phụ thuộc Ollama).

**Independent Test**: Playwright xanh cho luồng hỏi-đáp (SSE mock), bộ lọc lĩnh vực, cảnh báo hiệu lực.

**Acceptance Scenarios**:

1. **Given** app, **When** nhập câu hỏi và gửi, **Then** hiện danh sách nguồn + câu trả lời tăng dần.
2. **Given** câu ngoài phạm vi (stream chỉ có câu từ chối), **When** gửi, **Then** hiện đúng câu từ chối.
3. **Given** có ≥1 lĩnh vực, **When** mở trang, **Then** bộ lọc hiển thị; chọn lĩnh vực đổi truy vấn.

### Edge Cases

- SSE chia nhỏ giữa 1 dòng `data:` (chunk boundary) → parser phải ghép buffer đúng.
- Dòng SSE hỏng (JSON lỗi) → bỏ qua, không vỡ stream.
- E2E không được flaky: dùng chờ deterministic (chờ element/nội dung), không `waitForTimeout`.
- Unit test KHÔNG gọi mạng/Supabase thật (mock `fetch`/supabase client).

## Requirements *(mandatory)*

- **FR-001**: Thêm **unit test runner** + cấu hình chạy `.ts/.tsx` trong môi trường DOM; script `npm test`
  (+ `test:coverage`).
- **FR-002**: Unit test `lib/api.searchStream`: thứ tự event, ghép buffer chunk, bỏ dòng hỏng, lỗi HTTP/no-body,
  gửi `domain` trong body.
- **FR-003**: Unit test `useStreamQuery`: idle→loading→streaming→done; cộng dồn token; `error` giữa chừng;
  gọi `saveHistory` khi done; `reset`/abort.
- **FR-004**: Unit test `lib/history.saveHistory`: guest bỏ qua; đã đăng nhập map sources→refs + insert.
- **FR-005**: Unit test logic component: `LegalReference` (formatDate/docLabel/isAmended/cảnh báo/rỗng→null),
  `DomainFilter` (loading→chip, rỗng→null, onChange).
- **FR-006**: **E2E** luồng tra cứu deterministic (mock SSE): hỏi→nguồn+trả lời, từ chối, bộ lọc lĩnh vực.
  Giữ nguyên E2E auth+history hiện có (không hồi quy).
- **FR-007**: Test tích hợp CI (chạy trong workflow); unit test KHÔNG cần backend/Supabase; E2E ghi rõ phụ thuộc.
- **FR-008**: Coverage đơn vị ≥ **80%** cho `lib/`, `hooks/`, và logic thuần trong `components/`.

### Key Entities

- Không thêm entity nghiệp vụ. Chỉ hạ tầng test + test files.

## Success Criteria *(mandatory)*

- **SC-001**: `npm test` xanh; coverage ≥80% (lib/hooks/component-logic).
- **SC-002**: E2E Playwright (mock SSE) xanh cho luồng tra cứu + bộ lọc; auth/history không hồi quy.
- **SC-003**: Test chạy được trong CI; unit test < ~10s, không cần dịch vụ ngoài.
- **SC-004**: Không flaky (chạy lại 3 lần ổn định).

## Assumptions

- Next 16 breaking changes (AGENTS.md) — cấu hình test tránh phụ thuộc nội bộ Next; test tầng lib/hooks/logic.
- **Ngoài phạm vi (tùy clarify)**: visual regression baseline đầy đủ, a11y automation, cross-browser matrix,
  performance/Lighthouse gate — có thể thêm nhẹ hoặc để pha sau.
