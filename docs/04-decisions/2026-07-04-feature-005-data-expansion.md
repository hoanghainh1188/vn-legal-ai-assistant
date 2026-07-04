# Quyết định — Feature #5 (Pha 7): Mở rộng dữ liệu Luật Nhà ở

**Ngày**: 2026-07-04
**Feature**: `005-legal-data-expansion` (issue #5, roadmap epic #2 — Pha 7)

## D1 — Văn bản thêm (đã verify qua API Bộ Tư pháp)
Tất cả đều "Quy định chi tiết một số điều của Luật Nhà ở", hiệu lực 01/8/2024:

| Văn bản | ItemID | document_id | Số điều |
|---------|--------|-------------|---------|
| Nghị định 98/2024/NĐ-CP (cải tạo, xây dựng lại nhà chung cư) | 169711 | `98/2024/ND-CP` | 48 |
| Nghị định 100/2024/NĐ-CP (phát triển & quản lý nhà ở xã hội) | 169712 | `100/2024/ND-CP` | 78 |
| Thông tư 05/2024/TT-BXD (Bộ Xây dựng) | 169122 | `05/2024/TT-BXD` | 21 |

Corpus: 293 → **440 chunk** (198 Luật + 95 NĐ95 + 48 + 78 + 21). Verify: retrieval trích đúng văn bản
tương ứng (nhà ở xã hội → NĐ 100; cải tạo chung cư → NĐ 98), và **Điều 58 của Luật vẫn top-1** cho câu
hỏi thời hạn sở hữu (không bị điều cùng số của văn bản khác chiếm chỗ — nhờ khoá `(document_id, article_number)`
+ trích dẫn kèm số hiệu).

## D2 — KHÔNG nâng chunker cho phụ lục
- Kiểm định pipeline thật: cả 3 toàn văn API **không có điều trùng** (số điều liên tục 1..N).
- Phụ lục "Quy chế quản lý, sử dụng nhà chung cư" của TT 05 (đánh số Điều riêng) nằm ở **file đính kèm**,
  KHÔNG trong `vbpqToanVan` → không bị ingest → không xảy ra collision. Chunker giữ nguyên.
- **Ngoài phạm vi**: nội dung phụ lục/biểu mẫu; bổ sung là feature sau nếu cần (câu hỏi về chi tiết Quy chế
  quản lý chung cư có thể chưa được phủ).

## D3 — Sửa robustness embedding (phát sinh khi ingest dữ liệu mới)
- **Vấn đề**: NĐ 100 **Điều 38** (dày đặc danh sách/số) — 8000 ký tự tiếng Việt vượt giới hạn ~8192 token
  của bge-m3 → Ollama trả **500** dù đã cắt theo ký tự.
- **Sửa**: `OllamaEmbeddingProvider.embed_text` **thử lại với độ dài ngắn dần** (8000 → 6000 → 4000 → 2000)
  khi bị 500. Chỉ ảnh hưởng đúng điều bị lỗi; các điều khác + 293 chunk cũ embed ở độ dài đầy đủ → **không
  đổi embedding, không hồi quy**. Có test (`test_embed_text_retries_shorter_on_500`).

## D4 — Hiệu lực một phần (giới hạn đã biết)
- Cả 3 (và Luật, NĐ 95) đang "**Hết hiệu lực một phần**" — toàn văn API là **bản gốc**; một số điều có thể
  đã bị sửa bởi văn bản sau (vd NĐ 261/2025 sửa NĐ 100).
- **Chấp nhận ở giai đoạn này**; dùng bản **hợp nhất (VBHN)** cho chính xác tuyệt đối là việc lớn hơn, để sau.
  Disclaimer sẵn có trên UI đã nêu đây là công cụ tham khảo.

## Nguồn
- API mở Bộ Tư pháp `apipacs.moj.gov.vn/api/vbpl/document?id={ItemID}` (không đụng reCAPTCHA vbpl.vn).
- ItemID lấy từ URL vbpl.vn và verify số ký hiệu + trích yếu qua API.
