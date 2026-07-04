"""Factory chọn provider theo cấu hình (tĩnh, không fallback động).

Log INFO tên provider + model khi khởi tạo (KHÔNG log secret) — Principle V.
"""

import logging

from app.config import settings
from app.providers.base import ChatProvider, EmbeddingProvider
from app.providers.ollama import OllamaChatProvider, OllamaEmbeddingProvider

logger = logging.getLogger(__name__)
_logged: set[str] = set()


def _log_once(key: str, message: str) -> None:
    if key not in _logged:
        logger.info(message)
        _logged.add(key)


def get_chat_provider() -> ChatProvider:
    name = settings.chat_provider
    if name == "ollama":
        _log_once("chat:ollama", f"Chat provider: ollama (model={settings.llm_model})")
        return OllamaChatProvider()
    if name == "claude":
        if not settings.claude_api_key:
            raise ValueError(
                "chat_provider='claude' nhưng thiếu VN_LEGAL_CLAUDE_API_KEY "
                "(đặt qua biến môi trường)."
            )
        # Log tên provider + model, KHÔNG log key.
        _log_once("chat:claude", f"Chat provider: claude (model={settings.claude_model})")
        from app.providers.claude import ClaudeChatProvider

        return ClaudeChatProvider()
    raise ValueError(
        f"chat_provider không hợp lệ: {name!r}. Giá trị hợp lệ: ollama, claude"
    )


def get_embedding_provider() -> EmbeddingProvider:
    name = settings.embedding_provider
    if name == "ollama":
        _log_once(
            "embed:ollama", f"Embedding provider: ollama (model={settings.embed_model})"
        )
        return OllamaEmbeddingProvider()
    raise ValueError(
        f"embedding_provider không hợp lệ: {name!r}. Giá trị hợp lệ: ollama"
    )
