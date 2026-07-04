# Implementation Plan: Mở rộng dữ liệu — văn bản hướng dẫn Luật Nhà ở

**Branch**: `005-legal-data-expansion` | **Date**: 2026-07-04 | **Spec**: [spec.md](./spec.md)

## Summary

Thêm 3 văn bản (NĐ 98/2024, NĐ 100/2024, TT 05/2024) vào manifest `sources.py` và re-ingest.
**Không đổi code** — chunker/retrieval đã kiểm định chạy sạch trên cả 3 (không trùng số điều).
Corpus 293 → **440 chunk**. Bảo toàn hành vi RAG lõi.

## Technical Context

**Language/Version**: Python 3.12 · **Storage**: Postgres của Supabase (Pha 2), bảng `legal_chunks`.
**Testing**: pytest (chunker cho doc mới) + verify thủ công acceptance case.
**Constraints**: 3 acceptance case gốc + guarantee Điều 58 không hồi quy; trích dẫn kèm số hiệu văn bản.
**Scale/Scope**: chỉ sửa `backend/scripts/sources.py` (+3 entry) + re-ingest; +1 test chunker.

## Constitution Check

| Nguyên tắc | Đánh giá | Trạng thái |
|-----------|----------|-----------|
| I. Chống bịa | Trích dẫn kèm số hiệu VB (phân biệt điều cùng số); verify 3 case gốc | ✅ PASS (gate) |
| II. Verbatim | Toàn văn nguyên bản từ API Bộ Tư pháp; không sửa tay | ✅ PASS |
| III. Test-First & ≥80% | Thêm test chunker cho doc mới; backend coverage giữ | ✅ PASS |
| IV. Minh bạch | UI không đổi; disclaimer sẵn có | ✅ PASS |
| V. Riêng tư | Không đụng dữ liệu người dùng | ✅ PASS (N/A) |
| VI. Đơn giản | Chỉ mở rộng manifest, 0 đổi code xử lý | ✅ PASS |

## Project Structure

```text
backend/scripts/sources.py          # (sửa) +3 LegalSource: 169711, 169712, 169122
backend/tests/test_chunking.py       # (thêm) test chunker cho 1 văn bản mới (NĐ 100)
docs/architecture.md · README.md     # (sửa) phạm vi 4 văn bản, 440 chunk
docs/04-decisions/…-feature-005-…md  # (mới) ghi hiệu lực một phần + phụ lục TT05 ngoài phạm vi
```

**Structure Decision**: Feature dữ liệu thuần. Pipeline ingest hiện có (fetch API → chunk → embed →
upsert) tự xử lý văn bản mới. Không thêm module.

## Complexity Tracking
> Không vi phạm — feature tối giản, 0 abstraction mới.
