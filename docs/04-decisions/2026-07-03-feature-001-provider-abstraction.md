# Clarify — Feature #1: LLM Provider Abstraction (2026-07-03)

Các điểm mơ hồ trong intake được người dùng chốt trước khi viết `spec.md`
(`specs/001-llm-provider-abstraction/spec.md`). Ghi lại theo quy tắc: mọi câu trả lời
clarify phải lưu ở `docs/04-decisions/`.

## A1 — Phạm vi embedding provider
**Hỏi:** Feature này có làm bản embedding qua API không?
**Chốt:** KHÔNG. Chỉ làm `EmbeddingProvider` interface + hiện thực Ollama (bge-m3 self-host,
đúng lựa chọn kiến trúc "hybrid"). Provider embedding qua API để feature sau.

## A2 — Chuẩn hóa streaming của Claude
**Hỏi:** Map response streaming của Claude về dạng nào?
**Chốt:** Chuẩn hóa về cùng `AsyncIterator[str]` như Ollama — chỉ lấy phần text, bỏ qua
thinking/metadata. (Tương tự cách đã dùng `think=false` cho qwen3.5.)

## A3 — Cơ chế fallback
**Hỏi:** Có fallback (Claude lỗi → Ollama) ở feature này không?
**Chốt:** KHÔNG. Chọn provider tĩnh theo config. Fallback để feature sau.

## Q1 — Model Claude mặc định (từ /speckit-clarify)
**Hỏi:** Model Claude nào làm mặc định cho chat provider?
**Chốt:** `claude-sonnet-4-6` — cân bằng chất lượng/chi phí/độ trễ cho sản phẩm nhiều người
dùng; cấu hình được qua biến môi trường để nâng lên Opus khi cần.

## Q2 — Lỗi giữa chừng stream (từ /speckit-clarify)
**Hỏi:** Xử lý thế nào khi provider lỗi sau khi đã stream một phần token?
**Chốt:** Phát sự kiện SSE `error` rồi dừng luồng; client báo lỗi rõ ràng, KHÔNG trình bày
phần câu trả lời cắt dở như đã hoàn tất (bám Principle I). → thêm FR-011.

> Liên quan: kiến trúc hybrid (Constitution — Ràng buộc kỹ thuật), quyết định D2/D8 trong
> `2026-07-03-poc-tech-choices.md`.
