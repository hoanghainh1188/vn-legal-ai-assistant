# Research — Feature #1: LLM Provider Abstraction

Giải quyết các điểm kỹ thuật chưa chốt (gồm mục "Deferred" từ clarify: observability, timeout).

## R1 — Client cho ClaudeChatProvider: SDK `anthropic` vs httpx thô

- **Decision**: Dùng SDK `anthropic` (async) với `client.messages.stream(...)`, lấy text qua
  `stream.text_stream` (async iterator các chunk text).
- **Rationale**: SDK xử lý sẵn parse SSE của Anthropic, gộp delta text, phân biệt event
  (content_block_delta) — khớp trực tiếp với `AsyncIterator[str]` mà interface cần; ít mã
  thủ công, ít lỗi. Model mặc định `claude-sonnet-4-6` (quyết định Q1).
- **Alternatives**: httpx thô + tự parse SSE Anthropic — nhiều mã, dễ sai; bị loại vì
  Ollama đã dùng httpx nhưng Anthropic có SDK chính thức tốt hơn.

## R2 — Chuẩn hóa streaming về AsyncIterator[str] (A2)

- **Decision**: `ChatProvider.stream(system_prompt, user_message) -> AsyncIterator[str]` chỉ
  yield **text**. Với Claude: chỉ lấy `text_stream` (bỏ thinking/metadata). Với Ollama: giữ
  logic hiện tại (`think=false`, chỉ lấy `message.content`).
- **Rationale**: `rag.py` không cần biết provider nào; sự kiện SSE `token` giữ nguyên định dạng.

## R3 — Timeout cho Claude API (Deferred từ clarify)

- **Decision**: Cấu hình `claude_timeout` (mặc định 300s cho streaming), truyền vào client
  Anthropic. Khi timeout/lỗi mạng giữa chừng → coi là lỗi mid-stream (R6).
- **Rationale**: Streaming câu trả lời pháp lý có thể dài; 300s khớp timeout Ollama hiện tại
  (llm.py dùng 300s). Có thể chỉnh theo môi trường.

## R4 — Observability: log chọn provider (Deferred từ clarify)

- **Decision**: Log ở mức **INFO** khi factory khởi tạo provider: tên provider + model (KHÔNG
  log key). Log ở mức **ERROR** khi provider raise lỗi (thông điệp lỗi, KHÔNG log secret).
  Dùng `logging` chuẩn của Python (không thêm dependency).
- **Rationale**: Đủ để vận hành/gỡ lỗi biết đang chạy provider nào; tuân Principle V (không
  lộ secret). Quan sát nâng cao (metrics/tracing) để pha Production concerns sau.

## R5 — Số phận `services/llm.py`

- **Decision**: **Bỏ** `services/llm.py`; chuyển toàn bộ logic Ollama vào
  `providers/ollama.py`. `scripts/ingest.py` (đang gọi `llm.embed_texts`) chuyển sang dùng
  `get_embedding_provider()`.
- **Rationale**: Tránh hai đường dẫn code song song (Principle VI — đơn giản). `llm.py` chỉ
  là bọc mỏng; giữ lại gây trùng lặp.
- **Alternatives**: Giữ `llm.py` làm shim mỏng gọi provider — bị loại vì thêm gián tiếp thừa.
- **Ảnh hưởng test**: `test_rag.py` hiện patch `app.services.llm` → cập nhật sang patch
  provider/factory. Đây là thay đổi test được phép (test theo interface mới).

## R6 — Lỗi mid-stream → sự kiện SSE `error` (Q2 / FR-011)

- **Decision**: Trong `rag.search_stream`, bọc vòng lặp streaming trong try/except. Nếu lỗi
  xảy ra **sau khi** đã yield token: yield một sự kiện `data: {"type":"error","data":"..."}`
  rồi dừng (không yield `done`). Thông điệp lỗi thân thiện, không lộ chi tiết nhạy cảm.
- **Rationale**: Client phân biệt được "hoàn tất" (`done`) vs "lỗi giữa chừng" (`error`) →
  không trình bày phần dở như đầy đủ (Principle I). Cần thêm `type: "error"` vào schema SSE
  và xử lý ở frontend (`useStreamQuery` + hiển thị).

## R7 — Cấu hình môi trường (dev/prod)

- **Decision**: Giữ pydantic-settings + `.env` (đã có). Thêm biến: `chat_provider`,
  `embedding_provider` (default `ollama`), `claude_api_key` (không default), `claude_model`
  (default `claude-sonnet-4-6`), `claude_timeout` (default 300). Tài liệu hóa trong
  `.env.example`. Tách dev/prod bằng file `.env` theo môi trường (không commit `.env`).
- **Rationale**: Không thêm cơ chế config mới; đủ cho nhu cầu hiện tại.
