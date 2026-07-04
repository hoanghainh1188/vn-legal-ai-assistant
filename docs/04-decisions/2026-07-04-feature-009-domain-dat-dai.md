# Quyết định — Feature #9 (F2): Thêm lĩnh vực Đất đai

**Ngày**: 2026-07-04
**Feature**: `009-domain-dat-dai` (issue #9)

Feature dữ liệu đầu tiên trên nền đa lĩnh vực (F1) — kiểm chứng đa lĩnh vực chạy thật.

## Văn bản (xác minh API MOJ 2026-07-04)
| document_id | Tên | domain | eff_status | eff_date | ItemID | Số điều |
|-------------|-----|--------|-----------|----------|--------|---------|
| 31/2024/QH15 | Luật Đất đai 2024 | Đất đai | Hết hiệu lực một phần | 2025-01-01 | 177815 | 260 |

Corpus 440 → **700 chunk / 6 văn bản / 2 lĩnh vực**.

## Cơ chế (không đổi code — nền F1)
- Thêm 1 `LegalSource` + `domain="Đất đai"` vào `sources.py` → re-ingest.
- Chunker chạy sạch (260 điều, range 1-260, không trùng). Điều dài (>8000 ký tự) dùng retry embedding (Pha 7).

## Verify (đa lĩnh vực end-to-end)
- `/api/domains` = **["Đất đai", "Nhà ở"]** → bộ lọc UI tự có 2 lĩnh vực.
- Corpus theo lĩnh vực: Nhà ở 440, Đất đai 260.
- Câu đất đai (lọc "Đất đai") → trích **31/2024/QH15**.
- Lọc "Nhà ở" → **KHÔNG lẫn** điều Đất đai (cô lập lĩnh vực đúng).
- "Tất cả": Điều 58 (Luật Nhà ở) vẫn top-1 cho câu chung cư — **không hồi quy**.

## Ngoài phạm vi
- Nghị định/thông tư hướng dẫn Luật Đất đai (thêm sau nếu cần).
- Mở rộng lĩnh vực khác (lao động, doanh nghiệp…) — feature dữ liệu tương tự.
