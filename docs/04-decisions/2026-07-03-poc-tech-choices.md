# Quyết định kỹ thuật PoC — 2026-07-03

## D1: LLM Model → qwen3.5 (Ollama local)
- **Lý do**: Đã cài sẵn, multilingual tốt (tiếng Việt), 6.6GB vừa phải cho local inference
- **Thay thế nếu cần**: gemma4 (9.6GB, nặng hơn nhưng mạnh hơn)

## D2: Embedding Model → bge-m3 (Ollama) — CẬP NHẬT 2026-07-03
- **Ban đầu**: nomic-embed-text (nhẹ 261MB) — nhưng khi test với data thật, chất
  lượng semantic tiếng Việt yếu: câu hỏi "thời hạn **sở hữu** chung cư" xếp Điều 58
  ("thời hạn **sử dụng** nhà chung cư") ở hạng 64/293 → không vào context.
- **Đổi sang bge-m3** (1.2GB, 1024-dim, đa ngôn ngữ SOTA): cùng câu hỏi đó, bge-m3
  xếp Điều 58 **hạng 1/293**. Bắc cầu được ngữ nghĩa "sở hữu" ↔ "sử dụng".
- **Đánh đổi**: nặng hơn (1.2GB vs 261MB), embed chậm hơn, nhưng chất lượng retrieval
  vượt trội — đáng cho ứng dụng pháp lý.

## D2b: Hybrid retrieval (vector + lexical RRF)
- **Lý do**: Bổ sung cho embedder — kết hợp dense (bge-m3) với keyword BM25-lite
  (IDF-weighted), fusion bằng Reciprocal Rank Fusion, đảm bảo điều khớp tiêu đề luôn
  vào context. Kết quả cuối sắp theo relevance giảm dần.

## D2c: Cắt độ dài khi embed
- **Lý do**: Điều luật thật dài tới 14k ký tự vượt context model. Embed prefix đại
  diện (`max_embed_chars`), lưu full text cho hiển thị + LLM. Với bge-m3 (8192 token)
  đặt ngưỡng 8000 ký tự — đủ trọn hầu hết điều luật.

## D3: Vector DB → ChromaDB local
- **Lý do**: Đơn giản nhất cho PoC, không cần PostgreSQL, in-process
- **Exit path**: Migrate sang pgvector nếu scale lên production

## D4: Streaming → SSE (Server-Sent Events)
- **Lý do**: One-way streaming đủ cho RAG response, đơn giản hơn WebSocket
- **Pattern**: FastAPI StreamingResponse → Next.js API route proxy → ReadableStream ở client

## D5: Frontend-Backend communication → Next.js API route proxy
- **Lý do**: Tránh CORS issues, giữ Ollama URL server-side, clean API cho frontend
- **Pattern**: Client → /api/query (Next.js) → http://localhost:8000/api/query (FastAPI)

## D6: Chunking strategy → Split by "Điều" (Article)
- **Lý do**: Đơn vị pháp lý tự nhiên, mỗi Điều là một ý nghĩa trọn vẹn
- **Metadata**: article_number, article_title, document_id, chapter

## D7: Bỏ qua Spec Kit pipeline
- **Lý do**: PoC nhỏ, design doc đã rõ ràng, Spec Kit chưa cài (bootstrap.sh chưa chạy)
- **Vẫn tuân thủ**: Cấu trúc docs/, glossary, decisions log

## D8: Nguồn dữ liệu → API mở của Bộ Tư pháp (apipacs.moj.gov.vn)
- **Bối cảnh**: Toàn văn luật ở trên vbpl.vn, nhưng web UI có reCAPTCHA + Next.js
  server-action → `curl` không lấy được, ban đầu phải tải `body_content.html` bằng
  trình duyệt (thủ công).
- **Phát hiện**: Backend của vbpl.vn là API công khai **không cần auth**:
  `GET https://apipacs.moj.gov.vn/api/vbpl/document?id={ItemID}` trả toàn văn trong
  field `vbpqToanVan` (HTML). Đã xác minh: Luật (id=169032) → 198 điều, Nghị định
  (id=169709) → 95 điều.
- **Quyết định**: Fetch qua API này (`scripts/fetch_sources.py`), bỏ hoàn toàn bước
  tải tay. Manifest `sources.py` chỉ cần khai báo `vbpl_id`. Pipeline `ingest.py` tự
  fetch khi thiếu cache → tái lập 100% tự động từ repo sạch.
- **Cache**: HTML fetch về vẫn lưu `data/raw_html/` (commit) làm bản offline/nguồn
  tái lập, không phụ thuộc API lúc chạy lại.
