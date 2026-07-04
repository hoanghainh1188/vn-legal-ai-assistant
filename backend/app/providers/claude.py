"""Claude chat provider — streaming qua Anthropic API.

Chuẩn hóa đầu ra về cùng dạng AsyncIterator[str] như Ollama: chỉ yield text
(SDK `text_stream` đã bỏ metadata/thinking). Model + timeout theo config.
"""

from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from app.config import settings


class ClaudeChatProvider:
    def __init__(self) -> None:
        # Key được factory kiểm tra trước; kiểm tra lại để phòng thủ.
        if not settings.claude_api_key:
            raise ValueError("Thiếu claude_api_key để khởi tạo ClaudeChatProvider")
        self._client = AsyncAnthropic(
            api_key=settings.claude_api_key,
            timeout=settings.claude_timeout,
        )

    async def stream(
        self, system_prompt: str, user_message: str
    ) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens,
            temperature=0.1,  # nhất quán với Ollama; câu trả lời pháp lý ổn định
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
