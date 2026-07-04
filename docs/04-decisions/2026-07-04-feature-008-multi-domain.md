# Quyết định — Feature #8 (F1): Nền tảng đa lĩnh vực

**Ngày**: 2026-07-04
**Feature**: `008-multi-domain-foundation` (issue #8)

Bước F1 của hướng mở rộng ra ngoài Luật Nhà ở (đa lĩnh vực phổ thông, tăng dần, UI lọc lĩnh vực).

## D1 — Taxonomy lĩnh vực: **tự chọn, gán trong manifest**
- **Chọn**: nhóm lĩnh vực gọn, thân thiện người dân (vd "Nhà ở", "Đất đai", "Lao động", "Doanh nghiệp"…),
  gán thủ công `domain` cho mỗi văn bản trong `sources.py`. Corpus hiện tại → **"Nhà ở"**.
- **Loại bỏ**: field API `vbpqLinhVuc` — chuẩn nhà nước nhưng vụn/không đồng nhất, khó làm UX lọc gọn.
- **Lưu**: cột `domain` trên `legal_chunks` (giống eff_status) — migration + re-ingest.

## D2 — Danh sách lĩnh vực UI: **động từ DB** (`/api/domains`)
- **Chọn**: endpoint `GET /api/domains` trả `SELECT DISTINCT domain` (đang có trong kho). UI populate bộ lọc
  từ đây → **tự cập nhật** khi F2+ thêm lĩnh vực, không sửa/deploy lại UI.
- **Loại bỏ**: danh sách tĩnh trong config frontend (phải sửa tay mỗi lần thêm).

## D3 — Prompt tổng quát, GIỮ chống bịa
- Đổi phần **mở đầu** system prompt: bỏ "trợ lý về Luật Nhà ở" + liệt kê 5 văn bản → "trợ lý pháp luật
  Việt Nam, chỉ dùng Context". **GIỮ NGUYÊN** rules 1-6 (chỉ-dùng-Context, không nêu văn bản ngoài Context,
  từ chối an toàn, không bịa số) — vốn đã domain-agnostic.
- Câu từ chối `REFUSAL`: bỏ "Luật Nhà ở" → trung tính ("Dựa trên dữ liệu pháp luật hiện có…").
- **Gate (Constitution I)**: có test câu ngoài phạm vi vẫn từ chối; 3 acceptance case nhà ở không hồi quy.

## D4 — Retrieval lọc lĩnh vực
- `SearchRequest.domain` tùy chọn. Có → repository lọc `WHERE domain = %s` ở cả dense + all_rows; vắng/"Tất
  cả" → không lọc (hành vi hiện tại, 3 case gốc giữ nguyên).

## Ngoài phạm vi F1
- Thêm nội dung lĩnh vực mới (F2+). Đổi định vị trong **constitution** (tên "Trợ lý Luật Nhà ở") = file gác
  cổng → **PR steward riêng** (rule #5). F1 chỉ đụng code/dữ liệu/UI + CLAUDE.md/README.
