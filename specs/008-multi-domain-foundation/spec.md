# Feature Specification: Nền tảng đa lĩnh vực

**Feature Branch**: `008-multi-domain-foundation`

**Created**: 2026-07-04

**Status**: Draft

**Input**: Issue #8 — biến hệ thống thành đa-lĩnh-vực-capable (bước F1 của hướng mở rộng ra ngoài Luật
Nhà ở). Chưa thêm nội dung lĩnh vực mới; nhà ở là lĩnh vực #1.

## Clarifications

### Session 2026-07-04

- Q: Nguồn định danh **lĩnh vực** — taxonomy tự chọn hay field API `vbpqLinhVuc`? → A: **Taxonomy tự chọn**
  (gán thủ công trong `sources.py`); nhóm gọn cho người dân (vd "Nhà ở"). Corpus hiện tại = "Nhà ở".
- Q: Danh sách lĩnh vực cho bộ lọc UI? → A: **Động từ DB** — endpoint `/api/domains` trả `SELECT DISTINCT
  domain` → UI tự cập nhật khi F2+ thêm lĩnh vực (không sửa code UI).

## User Scenarios & Testing *(mandatory)*

> Giá trị: mở đường cho tra cứu nhiều lĩnh vực pháp luật, nhưng KHÔNG làm suy yếu chống bịa và KHÔNG
> hồi quy trải nghiệm nhà ở hiện có.

### User Story 1 - Tổng quát hoá (không còn khoá cứng "Luật Nhà ở") (Priority: P1)

Hệ thống tự định vị là trợ lý pháp luật Việt Nam (đa lĩnh vực), prompt không liệt kê cứng các văn bản
nhà ở; nhưng vẫn **chỉ trả lời từ Context** và **từ chối an toàn** khi thiếu dữ liệu.

**Why this priority**: Nền để thêm lĩnh vực khác. Rủi ro lớn nhất là tổng quát hoá làm LLM bịa — phải
giữ nguyên kỷ luật chống bịa (Constitution I).

**Independent Test**: 3 acceptance case gốc (nhà ở) vẫn đúng; câu ngoài phạm vi vẫn bị từ chối bằng câu
cố định (đã tổng quát, không nhắc "Luật Nhà ở").

**Acceptance Scenarios**:

1. **Given** prompt đã tổng quát, **When** hỏi câu nhà ở trong phạm vi, **Then** trả lời + trích dẫn đúng
   như trước (không hồi quy).
2. **Given** prompt đã tổng quát, **When** hỏi câu ngoài toàn bộ dữ liệu, **Then** từ chối an toàn bằng
   câu cố định (không bịa, không nêu văn bản ngoài Context).

---

### User Story 2 - Metadata lĩnh vực gắn với văn bản (Priority: P1)

Mỗi văn bản (và trích dẫn) gắn một **lĩnh vực** (vd "Nhà ở"). Trích dẫn hiển thị lĩnh vực để người dùng
biết ngữ cảnh.

**Why this priority**: Là dữ liệu nền cho bộ lọc + phân biệt lĩnh vực khi corpus mở rộng.

**Independent Test**: Tra một câu → mỗi trích dẫn kèm lĩnh vực; toàn bộ corpus nhà ở gắn đúng 1 lĩnh vực.

**Acceptance Scenarios**:

1. **Given** corpus hiện tại, **When** xem "Cơ sở pháp lý", **Then** mỗi trích dẫn hiện lĩnh vực (nhà ở).

---

### User Story 3 - Bộ lọc lĩnh vực (UI + retrieval) (Priority: P2)

Người dùng chọn lĩnh vực (hoặc "Tất cả") để thu hẹp tra cứu; retrieval chỉ lấy điều thuộc lĩnh vực đó.

**Why this priority**: Tăng độ chính xác khi có nhiều lĩnh vực (chống nhiễm chéo). P2 vì phụ thuộc US2.

**Independent Test**: Chọn lĩnh vực "Nhà ở" → kết quả chỉ thuộc nhà ở; chọn "Tất cả" → như hành vi hiện tại.

**Acceptance Scenarios**:

1. **Given** chọn một lĩnh vực, **When** tra cứu, **Then** retrieval chỉ trả điều thuộc lĩnh vực đó.
2. **Given** "Tất cả" (mặc định), **When** tra cứu, **Then** không lọc — giữ hành vi hiện tại (3 case gốc).

### Edge Cases

- Chọn lĩnh vực không có dữ liệu → trả rỗng an toàn + từ chối, không lỗi.
- Danh sách lĩnh vực khi mới chỉ có 1 (nhà ở) → bộ lọc vẫn hiển thị "Tất cả" + "Nhà ở" (không rỗng).
- Tổng quát prompt KHÔNG được nới lỏng chống bịa: câu ngoài phạm vi vẫn từ chối; không nhắc văn bản ngoài Context.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Mỗi văn bản PHẢI gắn một **lĩnh vực** (metadata); lưu cùng chunk (cột DB, giống eff_status);
  nguồn = manifest `sources.py`.
- **FR-002**: System prompt + câu từ chối PHẢI được **tổng quát hoá** (bỏ liệt kê cứng văn bản nhà ở),
  nhưng GIỮ NGUYÊN các quy tắc chống bịa + chỉ-dùng-Context + từ chối an toàn.
- **FR-003**: `SourceDocument` PHẢI kèm lĩnh vực để hiển thị.
- **FR-004**: Endpoint tra cứu PHẢI nhận tham số **lĩnh vực tùy chọn**; khi có → retrieval **chỉ lấy điều
  thuộc lĩnh vực đó**; khi vắng/"Tất cả" → không lọc (hành vi hiện tại).
- **FR-005**: Hệ thống PHẢI cung cấp **danh sách lĩnh vực** cho bộ lọc UI.
- **FR-006**: Frontend PHẢI có **bộ lọc lĩnh vực** (chọn/“Tất cả”) và tái định vị nhẹ (không còn tiêu đề
  khoá cứng "Luật Nhà ở"; nhà ở là lĩnh vực mặc định/hiện có).
- **FR-007**: 3 acceptance case gốc + guarantee Điều 58 PHẢI **không hồi quy** (mặc định "Tất cả").
- **FR-008**: Chống bịa (Constitution I) PHẢI không suy yếu: câu ngoài phạm vi vẫn từ chối; không nêu văn
  bản ngoài Context (có test).

### Key Entities

- **Domain (lĩnh vực)**: nhãn phân loại văn bản (vd "Nhà ở"). Gắn mỗi văn bản/chunk.
- **SourceDocument** (mở rộng): thêm `domain`.
- **SearchRequest** (mở rộng): thêm `domain` tùy chọn.

## Success Criteria *(mandatory)*

- **SC-001**: 3 acceptance case gốc + guarantee Điều 58 xanh với "Tất cả" (không hồi quy).
- **SC-002**: Câu ngoài phạm vi vẫn từ chối an toàn sau khi tổng quát prompt (test).
- **SC-003**: Chọn lĩnh vực "Nhà ở" → chỉ trả điều thuộc nhà ở; "Tất cả" → không lọc (test).
- **SC-004**: Mỗi trích dẫn hiển thị lĩnh vực; danh sách lĩnh vực có sẵn cho UI.
- **SC-005**: Coverage backend ≥ **80%**.

## Assumptions

- Chỉ **1 lĩnh vực** ("Nhà ở") ở F1 — nội dung lĩnh vực mới thêm ở F2+ (feature dữ liệu riêng).
- **Ngoài phạm vi**: thêm văn bản lĩnh vực mới; đổi định vị trong **constitution** (tên "Trợ lý Luật Nhà ở")
  — file gác cổng, cần **PR steward riêng** (rule #5). F1 chỉ đụng code/dữ liệu/UI + CLAUDE.md/README.
- Không đổi kiến trúc retrieval lõi (chỉ thêm điều kiện lọc lĩnh vực).
