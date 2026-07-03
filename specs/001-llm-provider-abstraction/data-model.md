# Data Model — Feature #1: LLM Provider Abstraction

Feature này không có thực thể lưu trữ (không đụng DB). "Mô hình" ở đây là các **hợp đồng
interface** và **cấu hình**.

## Interfaces (Protocol)

### ChatProvider
- `stream(system_prompt: str, user_message: str) -> AsyncIterator[str]`
  - Sinh câu trả lời **streaming**, chỉ yield các đoạn **text** (không metadata/thinking).

### EmbeddingProvider
- `embed_text(text: str) -> list[float]` — vector embedding cho một đoạn text.
- `embed_texts(texts: list[str]) -> list[list[float]]` — batch (tuần tự) cho ingest.

## Hiện thực

| Lớp | Interface | Ghi chú |
|-----|-----------|---------|
| `OllamaChatProvider` | ChatProvider | Port từ `llm.chat_stream` (qwen3.5, `think=false`, temp 0.1) |
| `OllamaEmbeddingProvider` | EmbeddingProvider | Port từ `llm.embed_text/embed_texts` (bge-m3, cắt `max_embed_chars`) |
| `ClaudeChatProvider` | ChatProvider | Anthropic SDK `messages.stream`, model `claude-sonnet-4-6`, timeout `claude_timeout` |

## Factory

- `get_chat_provider() -> ChatProvider` — trả provider theo `settings.chat_provider`.
- `get_embedding_provider() -> EmbeddingProvider` — theo `settings.embedding_provider`.
- Giá trị hợp lệ: `chat_provider ∈ {ollama, claude}`, `embedding_provider ∈ {ollama}` (A1).
- Giá trị lạ → raise `ValueError` liệt kê giá trị hợp lệ.
- `claude` mà thiếu `claude_api_key` → raise lỗi cấu hình rõ ràng (không lộ key).
- Log INFO tên provider + model khi khởi tạo (không log key).

## Config (mới thêm vào `Settings`, prefix `VN_LEGAL_`)

| Trường | Kiểu | Default | Ghi chú |
|--------|------|---------|---------|
| `chat_provider` | str | `ollama` | ollama \| claude |
| `embedding_provider` | str | `ollama` | ollama |
| `claude_api_key` | str \| None | `None` | từ env, KHÔNG hardcode |
| `claude_model` | str | `claude-sonnet-4-6` | |
| `claude_timeout` | float | `300.0` | giây, cho streaming |

## Trạng thái / vòng đời

Provider là **stateless**, chọn tĩnh lúc gọi factory theo config (A3 — không fallback động).
