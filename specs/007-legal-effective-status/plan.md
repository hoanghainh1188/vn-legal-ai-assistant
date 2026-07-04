# Implementation Plan: Nhãn hiệu lực + cảnh báo cấp văn bản

**Branch**: `007-legal-effective-status` | **Date**: 2026-07-04 | **Spec**: [spec.md](./spec.md)

## Summary

Thêm metadata hiệu lực cấp văn bản (`document_name`, `eff_status`, `eff_date`) vào `legal_chunks`
(cột DB), carry qua `SourceDocument`, hiển thị badge + **1 cảnh báo gộp** ở "Cơ sở pháp lý". Sửa
luôn bug nhãn văn bản (thông tư đang bị gán "NĐ"). Chỉ **cấp văn bản** — không suy diễn cấp điều
(API không có dữ liệu). Không đổi retrieval/RAG lõi.

## Technical Context

**Language/Version**: Python 3.12 (backend) · TypeScript/Next 16 (frontend).
**Storage**: Postgres Supabase — thêm cột vào `legal_chunks` (Supabase migration) + re-ingest 440.
**Testing**: pytest (hybrid_rank/repository carry metadata; SourceDocument) + frontend build/manual
(E2E tạm vướng port :3000 do twolody).
**Constraints**: RAG không đổi (3 acceptance case + Điều 58); KHÔNG khẳng định cấp điều (Constitution I);
metadata xác minh từ API MOJ (Constitution II).
**Scale/Scope**: migration + sources.py + repository/schemas/vector_store/ingest (carry 3 field) + 2 file
frontend (types, LegalReference).

## Constitution Check

| Nguyên tắc | Đánh giá | Trạng thái |
|-----------|----------|-----------|
| I. Chống bịa | Chỉ cấp văn bản; không suy diễn điều bị sửa; verify 3 case | ✅ PASS (gate) |
| II. Verbatim | Metadata hiệu lực lấy đúng từ API MOJ, xác minh | ✅ PASS |
| III. Test-First & ≥80% | Test carry metadata + cảnh báo viết trước | ✅ PASS (gate) |
| IV. Minh bạch | Cảnh báo hiệu lực = tăng minh bạch/an toàn | ✅ PASS |
| V. Riêng tư | Không đụng dữ liệu người dùng | ✅ PASS (N/A) |
| VI. Đơn giản | Denormalized cột, carry thẳng; không thêm service | ✅ PASS |

## Project Structure

```text
supabase/migrations/*_effective_status.sql   # (mới) +cột document_name/eff_status/eff_date
backend/
├── scripts/sources.py            # (sửa) +eff_status/eff_date mỗi LegalSource (xác minh API)
├── scripts/ingest.py             # (sửa) build ChunkRow kèm metadata
├── app/db/repository.py          # (sửa) ChunkRow/RetrievedRow +3 field; upsert/SELECT/_to_row
├── app/models/schemas.py         # (sửa) SourceDocument +document_name/eff_status/eff_date
└── app/services/vector_store.py  # (sửa) hybrid_rank dựng SourceDocument kèm metadata
frontend/
├── lib/types.ts                  # (sửa) SourceDocument +3 field
└── components/result/LegalReference.tsx  # (sửa) nhãn đúng + badge + 1 cảnh báo gộp
```

**Structure Decision**: Metadata đi cùng chunk (denormalized) từ manifest → DB → RetrievedRow →
SourceDocument → UI. `hybrid_rank` chỉ thêm field khi dựng SourceDocument (logic xếp hạng không đổi).
Cảnh báo là **suy ra ở frontend** từ `eff_status` của các nguồn (gộp 1 lần).

## Ghi chú
- **eff_date** kiểu `date` (nullable); **eff_status/document_name** `text`.
- Upsert `ON CONFLICT DO UPDATE` phải cập nhật cả 3 cột mới (ingest lại đổi metadata được).
- Xác minh `eff_status` của **NĐ 95/2024** (chưa cache) khi implement, trước khi điền manifest.
- Re-ingest: re-embed 440 (chấp nhận) — nguồn sự thật manifest → DB.

## Complexity Tracking
> Không vi phạm — mở rộng dữ liệu tuyến tính, 0 abstraction mới.
