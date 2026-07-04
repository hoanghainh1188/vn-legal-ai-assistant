# Feature Specification: Mở rộng dữ liệu — văn bản hướng dẫn Luật Nhà ở 2023

**Feature Branch**: `005-legal-data-expansion`

**Created**: 2026-07-04

**Status**: Draft

**Input**: Issue #5 — thêm bộ văn bản quy định chi tiết Luật Nhà ở 2023 vào phạm vi tra cứu
(roadmap epic #2, Pha 7).

## Clarifications

### Session 2026-07-04

- Q: Thêm những văn bản nào? → A: **NĐ 98/2024/NĐ-CP** (cải tạo/xây lại chung cư, ItemID 169711),
  **NĐ 100/2024/NĐ-CP** (nhà ở xã hội, 169712), **TT 05/2024/TT-BXD** (169122) — đều "quy định chi tiết
  một số điều của Luật Nhà ở", đã verify qua API Bộ Tư pháp.
- Q: Có cần nâng chunker cho phụ lục TT 05 không? → A: **KHÔNG** — kiểm định pipeline thật: cả 3 toàn văn
  không có điều trùng (48/78/21 điều, range liên tục). Phụ lục "Quy chế" nằm ở file đính kèm, không trong
  toàn văn API → không ingest ở feature này.

## User Scenarios & Testing *(mandatory)*

> "Người dùng" là người dân tra cứu: mở rộng phạm vi để trả lời được câu hỏi về nhà ở xã hội, cải tạo
> chung cư, và hướng dẫn của Bộ Xây dựng — không chỉ Luật + NĐ 95.

### User Story 1 - Tra cứu được văn bản mới (Priority: P1)

Người dùng hỏi về chủ đề thuộc văn bản mới (vd điều kiện mua nhà ở xã hội, cải tạo chung cư cũ) và hệ
thống trích dẫn đúng điều/khoản từ NĐ 100 / NĐ 98 / TT 05.

**Why this priority**: Đây là giá trị của feature — mở rộng phạm vi trả lời.

**Independent Test**: Hỏi một câu thuộc NĐ 100 (nhà ở xã hội) → câu trả lời trích đúng điều của
`100/2024/NĐ-CP`.

**Acceptance Scenarios**:

1. **Given** dữ liệu đã nạp lại, **When** hỏi "Điều kiện được mua nhà ở xã hội là gì?", **Then** hệ thống
   trích dẫn điều từ **NĐ 100/2024/NĐ-CP**.
2. **Given** dữ liệu đã nạp lại, **When** hỏi về cải tạo/xây lại chung cư cũ, **Then** trích từ **NĐ 98/2024/NĐ-CP**.

---

### User Story 2 - Không hồi quy phạm vi cũ (Priority: P1)

Sau khi thêm dữ liệu, 3 acceptance case gốc (Luật Nhà ở) vẫn đúng — không bị "nhiễu" bởi văn bản mới.

**Why this priority**: Ràng buộc bất khả xâm phạm (Constitution I). Thêm dữ liệu không được làm hỏng
retrieval hiện có.

**Independent Test**: Chạy 3 acceptance case gốc trên corpus mở rộng; guarantee Điều 58 (Luật) vẫn giữ.

**Acceptance Scenarios**:

1. **Given** corpus 440 chunk, **When** hỏi "Chung cư có thời hạn sở hữu tối đa bao nhiêu năm?", **Then**
   vẫn surface **Điều 58 của Luật Nhà ở** (không bị điều cùng số của văn bản khác chiếm chỗ).
2. **Given** corpus mở rộng, **When** hỏi câu ngoài phạm vi, **Then** vẫn từ chối an toàn.

### Edge Cases

- Nhiều văn bản có cùng **số điều** (vd Điều 1 ở cả 4 văn bản) → retrieval + trích dẫn phải **kèm số hiệu
  văn bản** để không nhầm nguồn (khoá lưu trữ là `(document_id, article_number)`).
- Văn bản "Hết hiệu lực một phần" → toàn văn là bản gốc; một số điều có thể đã bị sửa. Cần ghi nhận hạn chế.
- Ingest chạy lại phải idempotent — không nhân bản.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI nạp thêm 3 văn bản (NĐ 98/2024, NĐ 100/2024, TT 05/2024) vào corpus, mỗi điều
  là 1 chunk với `document_id` = số hiệu văn bản.
- **FR-002**: Truy hồi + trích dẫn PHẢI **kèm số hiệu văn bản** để phân biệt các điều cùng số ở các văn bản
  khác nhau (không nhầm nguồn — Constitution I).
- **FR-003**: 3 acceptance case gốc + guarantee Điều 58 (Luật Nhà ở) PHẢI **không hồi quy**.
- **FR-004**: Ingest PHẢI idempotent (chạy lại không nhân bản); tổng corpus = **440 chunk** (293 + 147).
- **FR-005**: Nội dung điều luật PHẢI lấy **nguyên văn** từ API Bộ Tư pháp (Constitution II); nguồn khai
  báo trong `sources.py`.
- **FR-006**: KHÔNG đổi code xử lý (chunker/retrieval) — chỉ mở rộng manifest dữ liệu (đã kiểm định an toàn).

### Key Entities

- **LegalSource** (manifest): `vbpl_id, html, text, document_id, name` — thêm 3 entry.
- **LegalChunk**: không đổi cấu trúc.

## Success Criteria *(mandatory)*

- **SC-001**: Corpus = **440 chunk** sau re-ingest (Luật 198 + NĐ95 95 + NĐ98 48 + NĐ100 78 + TT05 21).
- **SC-002**: Câu hỏi thuộc NĐ 100 / NĐ 98 trích đúng văn bản tương ứng (test/thủ công).
- **SC-003**: 3 acceptance case gốc + guarantee Điều 58 vẫn xanh (không hồi quy).
- **SC-004**: Ingest idempotent (chạy 2 lần → vẫn 440).
- **SC-005**: Test chunker cho ≥1 văn bản mới (số điều đúng, không trùng).

## Assumptions

- Dùng **API mở Bộ Tư pháp** (apipacs.moj.gov.vn) — không đụng reCAPTCHA vbpl.vn.
- **Phụ lục** (Quy chế quản lý chung cư của TT 05, biểu mẫu) **ngoài phạm vi** — chỉ ingest thân văn bản
  (toàn văn API). Bổ sung phụ lục là feature sau nếu cần.
- Văn bản "Hết hiệu lực một phần": chấp nhận bản gốc ở giai đoạn này; dùng bản hợp nhất (VBHN) là việc sau.
- Không đổi kiến trúc/retrieval; embedding vẫn bge-m3.
