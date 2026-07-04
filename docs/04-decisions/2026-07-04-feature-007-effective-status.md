# Quyết định — Feature #7: Nhãn hiệu lực + cảnh báo cấp văn bản

**Ngày**: 2026-07-04
**Feature**: `007-legal-effective-status` (issue #7)

## D1 — Phạm vi: chỉ **cấp văn bản** (không cấp điều)
- **Khảo sát API MOJ** (endpoint document + lược đồ `qtdc/public/doc/{id}`):
  - `effStatus` + `effFrom` (trạng thái + ngày hiệu lực) **có sẵn cấp văn bản**.
  - `references` liệt kê văn bản liên quan nhưng **`referenceProvisions` rỗng toàn bộ** → KHÔNG có dữ liệu
    "điều X bị sửa bởi VB Y".
- **Quyết định**: chỉ hiển thị/cảnh báo **cấp văn bản**. TUYỆT ĐỐI không suy diễn cấp điều (Constitution I —
  chống bịa). Bịa "Điều 58 đã bị sửa" còn tệ hơn không hiển thị.
- **Ngoài phạm vi**: mapping cấp điều, chỉ đích danh văn bản sửa đổi, bản hợp nhất (VBHN).

## D2 — Lưu metadata: **cột DB trên `legal_chunks`** (denormalized)
- **Chọn**: thêm cột `document_name`, `eff_status`, `eff_date` vào `legal_chunks` qua Supabase migration.
- Nguồn sự thật = manifest `backend/scripts/sources.py`: đã có `name`; thêm `eff_status`/`eff_date` (xác minh
  từ API MOJ). Ingest populate cột; **re-ingest** để backfill 440 chunk.
- **Lý do**: người dùng chọn cột DB (nhất quán, sẵn sàng nếu sau này cần lọc theo hiệu lực).
- **Loại bỏ**: config/manifest lookup runtime (không đổi schema) — đơn giản hơn nhưng người dùng ưu tiên DB.

## Metadata đã xác minh (từ API, 2026-07-04)
| document_id | Tên | eff_status | eff_date |
|-------------|-----|-----------|----------|
| 27/2023/QH15 | Luật Nhà ở 2023 | Hết hiệu lực một phần | 2024-08-01 |
| 95/2024/ND-CP | Nghị định 95/2024/NĐ-CP | Hết hiệu lực một phần | 2024-08-01 |
| 98/2024/ND-CP | Nghị định 98/2024/NĐ-CP | Hết hiệu lực một phần | 2024-08-01 |
| 100/2024/ND-CP | Nghị định 100/2024/NĐ-CP | Hết hiệu lực một phần | 2024-08-01 |
| 05/2024/TT-BXD | Thông tư 05/2024/TT-BXD | Hết hiệu lực một phần | 2024-08-01 |

## D3 — UI: nhãn + 1 cảnh báo gộp
- `SourceDocument` mở rộng: `document_name`, `eff_status` (+ `eff_date`).
- `LegalReference`: sửa nhãn văn bản (đang hardcode sai — thông tư bị gán "NĐ"); thêm badge trạng thái;
  gộp **1** cảnh báo khi có ≥1 trích dẫn "hết hiệu lực một phần/toàn bộ".
- Cảnh báo trung tính, không chỉ đích danh điều/văn bản sửa (D1).
