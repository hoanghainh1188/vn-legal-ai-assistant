"""Provider interfaces (Protocol) — hợp đồng cho chat và embedding.

Xem contracts: specs/001-llm-provider-abstraction/contracts/providers.md
"""

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class ChatProvider(Protocol):
    """Sinh câu trả lời streaming dưới dạng luồng token TEXT."""

    def stream(
        self, system_prompt: str, user_message: str
    ) -> AsyncIterator[str]:
        """Trả về một AsyncIterator các đoạn text (không metadata/thinking).

        Hiện thực là **async generator** (`async def stream(...): ... yield ...`);
        vì vậy annotation ở đây là `def ... -> AsyncIterator[str]` (gọi `stream()`
        trả iterator ngay, KHÔNG await lời gọi). Caller dùng
        `async for token in provider.stream(...)`.
        """
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Sinh vector embedding cho text."""

    async def embed_text(self, text: str) -> list[float]:
        ...

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...
