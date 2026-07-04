# Feature Specification: Thêm lĩnh vực Đất đai

**Feature Branch**: `009-domain-dat-dai`

**Created**: 2026-07-04

**Status**: Draft

**Input**: Issue #9 — thêm lĩnh vực thứ 2 (Đất đai) để kiểm chứng nền tảng đa lĩnh vực (F1) chạy thật.
Feature dữ liệu, không đổi code.

## Clarifications

### Session 2026-07-04

- Q: Lĩnh vực & văn bản? → A: **Đất đai** — Luật Đất đai 2024 (31/2024/QH15, ItemID 177815), xác minh API
  MOJ (Hết hiệu lực một phần, hiệu lực 01/01/2025, 260 điều).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tra cứu được lĩnh vực Đất đai (Priority: P1)

Người dùng chọn lĩnh vực "Đất đai" (hoặc "Tất cả") và hỏi về đất đai → hệ thống trích dẫn đúng điều của
Luật Đất đai 2024; bộ lọc UI tự hiển thị lĩnh vực mới.

**Independent Test**: `/api/domains` gồm "Đất đai" + "Nhà ở"; hỏi câu đất đai (lọc "Đất đai") → trích
`31/2024/QH15`.

**Acceptance Scenarios**:

1. **Given** đã nạp Đất đai, **When** hỏi "Đất nông nghiệp gồm những loại nào?" (lọc Đất đai), **Then**
   trích điều từ Luật Đất đai 2024.
2. **Given** bộ lọc, **When** mở trang, **Then** thấy chip "Tất cả" + "Đất đai" + "Nhà ở".

### User Story 2 - Không hồi quy lĩnh vực Nhà ở (Priority: P1)

Thêm Đất đai không làm hỏng nhà ở: 3 acceptance case gốc + guarantee Điều 58 giữ nguyên; lọc "Nhà ở"
chỉ trả nhà ở (không lẫn đất đai).

**Independent Test**: 3 case nhà ở ("Tất cả") xanh; lọc "Nhà ở" → không có điều Đất đai.

### Edge Cases

- Điều cùng số ở 2 văn bản/lĩnh vực (vd Điều 3 ở cả Luật Nhà ở và Đất đai) → phân biệt bằng
  `(document_id, article_number)` + trích dẫn kèm số hiệu (đã có).
- Lọc "Nhà ở" → tuyệt đối không trả điều thuộc "Đất đai" (nhiễm chéo).

## Requirements *(mandatory)*

- **FR-001**: Thêm Luật Đất đai 2024 (177815) vào manifest với `domain="Đất đai"`; re-ingest → tổng **700 chunk**.
- **FR-002**: `/api/domains` PHẢI gồm "Đất đai" và "Nhà ở".
- **FR-003**: Lọc theo lĩnh vực PHẢI cô lập đúng: "Đất đai" chỉ Đất đai, "Nhà ở" chỉ nhà ở.
- **FR-004**: 3 acceptance case gốc + guarantee Điều 58 (nhà ở) PHẢI không hồi quy ("Tất cả").
- **FR-005**: Nội dung nguyên văn từ API MOJ (Constitution II); KHÔNG đổi code xử lý.

## Success Criteria *(mandatory)*

- **SC-001**: Corpus = **700 chunk** (440 + 260); `/api/domains` = ["Đất đai", "Nhà ở"].
- **SC-002**: Câu đất đai (lọc Đất đai) trích `31/2024/QH15`; lọc Nhà ở không lẫn đất đai.
- **SC-003**: 3 acceptance case nhà ở + Điều 58 không hồi quy.
- **SC-004**: Backend test xanh (coverage ≥80%).

## Assumptions

- Bản gốc "hết hiệu lực một phần" (như các văn bản khác) — nhãn hiệu lực (Feature #7) hiển thị đúng.
- **Ngoài phạm vi**: nghị định/thông tư hướng dẫn Luật Đất đai (thêm sau nếu cần); mapping cấp điều.
