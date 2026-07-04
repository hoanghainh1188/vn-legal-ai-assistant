# Feature Specification: Nhãn hiệu lực + cảnh báo cấp văn bản

**Feature Branch**: `007-legal-effective-status`

**Created**: 2026-07-04

**Status**: Draft

**Input**: Issue #7 — tăng độ tin cậy pháp lý: hiển thị trạng thái hiệu lực + cảnh báo cho mỗi trích dẫn.
Vá điểm yếu Pha 7 (trả lời từ bản gốc văn bản "hết hiệu lực một phần" mà không cảnh báo).

## Clarifications

### Session 2026-07-04

- Q: Lưu metadata hiệu lực (effStatus/effFrom/tên) ở đâu? → A: **Cột DB trên `legal_chunks`** (denormalized)
  — thêm cột `document_name`, `eff_status`, `eff_date` qua Supabase migration; nguồn = manifest `sources.py`
  (đã có `name`, thêm `eff_status`/`eff_date` xác minh từ API); ingest populate; **re-ingest** để backfill.

## User Scenarios & Testing *(mandatory)*

> Giá trị: người dân thấy được **trạng thái hiệu lực** của điều luật được trích, và được **cảnh báo** khi
> văn bản đã bị sửa một phần — để không hiểu nhầm rằng câu trả lời là quy định mới nhất tuyệt đối.

### User Story 1 - Hiện trạng thái hiệu lực + tên văn bản đúng (Priority: P1)

Mỗi mục trong "Cơ sở pháp lý" hiển thị **tên văn bản đầy đủ** và **trạng thái hiệu lực** (vd "Hết hiệu
lực một phần", "Còn hiệu lực") kèm ngày hiệu lực.

**Why this priority**: Đây là thông tin nền để người dùng đánh giá độ tin cậy của trích dẫn. Cũng sửa
lỗi hiện tại: UI đang gán sai nhãn (mọi văn bản không phải Luật đều thành "NĐ ...", kể cả Thông tư).

**Independent Test**: Tra một câu, mở "Cơ sở pháp lý" → mỗi trích dẫn hiện tên văn bản đúng (Luật/NĐ/TT)
+ trạng thái hiệu lực.

**Acceptance Scenarios**:

1. **Given** kết quả có trích Điều thuộc Luật Nhà ở 2023, **When** xem "Cơ sở pháp lý", **Then** hiện
   "Luật Nhà ở 2023" + "Hết hiệu lực một phần".
2. **Given** trích Điều thuộc Thông tư 05/2024/TT-BXD, **When** xem, **Then** hiện "Thông tư 05/2024/TT-BXD"
   (KHÔNG bị gán nhầm "NĐ").

---

### User Story 2 - Cảnh báo khi văn bản đã bị sửa một phần (Priority: P1)

Khi câu trả lời trích từ văn bản đang "Hết hiệu lực một phần" (hoặc hết hiệu lực toàn bộ), hệ thống hiển
thị **cảnh báo** ngắn: một số quy định có thể đã được sửa đổi, nên kiểm tra văn bản mới nhất.

**Why this priority**: Đây là giá trị "độ tin cậy" cốt lõi (Constitution IV — minh bạch/an toàn). Không
cảnh báo dễ khiến người dùng tin nhầm bản cũ là mới nhất.

**Independent Test**: Tra câu trích từ văn bản "hết hiệu lực một phần" → thấy cảnh báo; nếu tất cả trích
dẫn "còn hiệu lực" → không cảnh báo (không gây nhiễu thừa).

**Acceptance Scenarios**:

1. **Given** ≥1 trích dẫn thuộc văn bản "Hết hiệu lực một phần", **When** xem kết quả, **Then** hiện cảnh
   báo hiệu lực rõ ràng.
2. **Given** cảnh báo, **When** đọc, **Then** KHÔNG chỉ đích danh điều/văn bản sửa đổi (vì không có dữ liệu
   cấp điều — không được bịa).

### Edge Cases

- Văn bản không có trong bảng metadata (trường hợp lạ) → hiển thị trung tính, không cảnh báo sai, không lỗi.
- KHÔNG suy diễn cấp điều: API không cho biết điều nào bị sửa (`referenceProvisions` rỗng) → chỉ nói cấp
  văn bản, tuyệt đối không "Điều X đã bị sửa" (Constitution I).
- Cảnh báo không được lặp lại rối mắt nếu nhiều trích dẫn cùng trạng thái — gộp 1 cảnh báo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI có metadata mỗi văn bản: **tên hiển thị**, **trạng thái hiệu lực**, **ngày
  hiệu lực** — lấy từ nguồn chính thống (API MOJ), xác minh, không bịa.
- **FR-002**: Mỗi `SourceDocument` trả về PHẢI kèm tên văn bản + trạng thái hiệu lực để hiển thị.
- **FR-003**: Frontend "Cơ sở pháp lý" PHẢI hiển thị tên văn bản **đúng loại** (Luật/Nghị định/Thông tư)
  cho mọi văn bản trong corpus, không hardcode sai.
- **FR-004**: Khi ≥1 trích dẫn thuộc văn bản "hết hiệu lực một phần/toàn bộ", frontend PHẢI hiển thị
  **một** cảnh báo hiệu lực (gộp, không lặp).
- **FR-005**: Cảnh báo + nhãn PHẢI **chỉ ở cấp văn bản**; TUYỆT ĐỐI không khẳng định điều/khoản cụ thể nào
  đã bị sửa (không đủ dữ liệu — Constitution I).
- **FR-006**: Hành vi RAG lõi (retrieval, prompt, luồng SSE) PHẢI **không đổi**; 3 acceptance case gốc +
  guarantee Điều 58 giữ nguyên.
- **FR-007**: (tùy chọn) Có thể đưa trạng thái hiệu lực vào context để LLM trả lời thận trọng hơn — nhưng
  KHÔNG được khiến LLM bịa chi tiết sửa đổi.

### Key Entities

- **DocumentMeta**: `document_id → {display_name, eff_status, eff_date}` — metadata tĩnh, xác minh từ API.
- **SourceDocument** (mở rộng): thêm `document_name`, `eff_status` (và `eff_date` nếu cần) để frontend hiển thị.

## Success Criteria *(mandatory)*

- **SC-001**: Mọi trích dẫn hiện tên văn bản đúng loại (Luật/NĐ/TT) + trạng thái hiệu lực (test + thủ công).
- **SC-002**: Có ≥1 trích dẫn "hết hiệu lực một phần" → hiện đúng 1 cảnh báo; không có → không cảnh báo.
- **SC-003**: Không có khẳng định cấp điều về sửa đổi ở bất kỳ đâu (rà soát prompt/UI/metadata).
- **SC-004**: 3 acceptance case gốc + guarantee Điều 58 vẫn xanh (không hồi quy).
- **SC-005**: Coverage backend ≥ **80%**.

## Assumptions

- Metadata hiệu lực **tĩnh, xác minh từ API MOJ** (5 văn bản) — cập nhật khi thêm văn bản mới. Không fetch
  live mỗi query.
- **Ngoài phạm vi**: mapping cấp điều, chỉ đích danh văn bản sửa đổi, bản hợp nhất VBHN, tự động cập nhật
  trạng thái theo thời gian thực.
- Không đổi kiến trúc retrieval/embedding.
