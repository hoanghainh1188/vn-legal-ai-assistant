# Intake — Feature #1: LLM Provider Abstraction

> Feature refactor nền tảng (Pha 0 — Hardening). Không có tài liệu thiết kế khách hàng;
> brief này do agent soạn, đóng vai trò output của `design-intake` để làm input cho
> `/speckit-specify`. Issue: #1 · Branch: `001-llm-provider-abstraction`.

## Bối cảnh

Dự án đang chuyển từ PoC sang sản phẩm thật với kiến trúc AI **hybrid**: embedding
self-host (`bge-m3`) + chat qua **Claude API**. Hiện tại `backend/app/services/llm.py`
gọi Ollama trực tiếp cho cả embedding lẫn chat, và `services/rag.py` phụ thuộc cứng vào
module này. Để đổi nhà cung cấp chat (Ollama → Claude) mà không phải sửa business logic
RAG, cần đưa provider ra sau một lớp abstraction (Constitution — Principle VI).

## Mục tiêu

Tách nhà cung cấp LLM/embedding thành các interface, cho phép chọn provider qua cấu hình
theo môi trường, **không thay đổi hành vi mặc định hiện tại** (Ollama vẫn là default →
không phá 27 test và 3 acceptance case).

## Prompt for /speckit-specify

Tạo đặc tả cho tính năng "Lớp abstraction nhà cung cấp LLM/embedding" của backend trợ lý
tra cứu Luật Nhà ở:

- Định nghĩa hai giao thức (interface): `ChatProvider` (streaming chat) và
  `EmbeddingProvider` (sinh vector embedding cho một đoạn text).
- Cung cấp các hiện thực: `OllamaChatProvider` và `OllamaEmbeddingProvider` giữ nguyên
  hành vi hiện tại (gọi Ollama `qwen3.5` / `bge-m3`); `ClaudeChatProvider` gọi Claude API
  để streaming chat.
- Chọn nhà cung cấp qua cấu hình (biến môi trường): `chat_provider` và `embedding_provider`,
  mặc định đều là `ollama`. Khi `chat_provider=claude`, dùng Claude API với khóa lấy từ
  biến môi trường (không hardcode secret).
- `services/rag.py` chỉ phụ thuộc vào interface (thông qua một factory chọn provider theo
  config), không import Ollama trực tiếp.
- Tách cấu hình theo môi trường (dev/prod) và tài liệu hóa biến môi trường trong
  `.env.example`.
- Ràng buộc: KHÔNG thay đổi phạm vi RAG (retrieval, prompt, luồng SSE) — chỉ tái cấu trúc
  cách gọi provider. Hành vi khi dùng Ollama phải giống hệt hiện tại.

## Tiêu chí acceptance ("xong")

1. `rag.py` không còn import `services/llm.py`/Ollama trực tiếp; đi qua interface + factory.
2. Mặc định (Ollama): 27 test cũ + 3 acceptance case (chung cư / việt kiều / ngoài phạm vi)
   vẫn xanh, hành vi không đổi.
3. `ClaudeChatProvider` có hiện thực streaming; chọn được qua config (không cần key để
   chạy default Ollama).
4. Có test mới cho: factory chọn đúng provider theo config; provider raise lỗi rõ ràng khi
   thiếu cấu hình/secret.
5. Không hardcode secret; `.env.example` liệt kê biến mới. Coverage ≥ 80%.

## Ambiguities (cho /speckit-clarify)

- **A1 — Embedding provider có cần bản Claude/API ngay không?** Người dùng chọn "hybrid"
  = embedding self-host. Đề xuất: chỉ làm `EmbeddingProvider` interface + Ollama impl ở
  feature này; provider embedding qua API để sau. Cần xác nhận.
- **A2 — Xử lý "thinking mode" của Claude khi streaming?** Cần thống nhất cách map response
  streaming của Claude về cùng dạng token generator như Ollama (đã dùng `think=false` cho
  qwen3.5).
- **A3 — Có cần cơ chế fallback** (Claude lỗi → tự chuyển Ollama) ở feature này, hay chỉ
  chọn tĩnh theo config? Đề xuất: chọn tĩnh trước, fallback để sau.
