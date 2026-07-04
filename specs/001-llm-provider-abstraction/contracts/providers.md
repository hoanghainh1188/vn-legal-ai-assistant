# Contracts — Feature #1: Provider interfaces & SSE

## Interface: ChatProvider

```python
from collections.abc import AsyncIterator
from typing import Protocol

class ChatProvider(Protocol):
    # Hiện thực là async generator (async def + yield); annotation là
    # `def ... -> AsyncIterator[str]` vì gọi stream() trả iterator ngay (không await).
    def stream(
        self, system_prompt: str, user_message: str
    ) -> AsyncIterator[str]:
        """Trả về AsyncIterator các đoạn TEXT (không metadata/thinking)."""
        ...
```

**Hợp đồng hành vi:**
- Chỉ yield text; không yield chuỗi rỗng do thinking.
- Lỗi mạng/timeout → raise exception (được `rag` bắt và chuyển thành sự kiện SSE `error`).

## Interface: EmbeddingProvider

```python
from typing import Protocol

class EmbeddingProvider(Protocol):
    async def embed_text(self, text: str) -> list[float]: ...
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
```

**Hợp đồng hành vi:**
- `embed_text` cắt input theo `max_embed_chars` trước khi gọi model (giữ hành vi hiện tại).
- Trả vector cùng số chiều với model đang cấu hình (bge-m3 = 1024).

## Factory

```python
def get_chat_provider() -> ChatProvider: ...
def get_embedding_provider() -> EmbeddingProvider: ...
```

- Chọn theo `settings.chat_provider` / `settings.embedding_provider`.
- Giá trị không hợp lệ → `ValueError` (liệt kê giá trị hợp lệ).
- `chat_provider="claude"` mà thiếu `claude_api_key` → `ValueError`/lỗi cấu hình rõ ràng.

## SSE schema (mở rộng)

Luồng `/api/query` giữ nguyên các sự kiện hiện có, **thêm** sự kiện `error`:

| type | data | Khi nào |
|------|------|---------|
| `sources` | `SourceDocument[]` | sau retrieval (không đổi) |
| `token` | `string` | mỗi đoạn text (không đổi) |
| `done` | `""` | hoàn tất bình thường (không đổi) |
| `error` | `string` (thông điệp thân thiện) | **MỚI** — lỗi giữa chừng stream (FR-011); không kèm `done` |

Frontend: `useStreamQuery` xử lý `error` → set trạng thái lỗi, KHÔNG coi phần token đã nhận
là câu trả lời hoàn chỉnh.
