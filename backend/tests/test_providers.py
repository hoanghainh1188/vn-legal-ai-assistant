"""Tests cho lớp provider abstraction (factory + Ollama/Claude providers)."""

import logging

import httpx
import pytest
import respx

from app.config import settings
from app.providers import factory
from app.providers.base import ChatProvider, EmbeddingProvider
from app.providers.ollama import OllamaChatProvider, OllamaEmbeddingProvider


class TestFactoryDefaults:
    def test_defaults_to_ollama(self) -> None:
        assert isinstance(factory.get_chat_provider(), OllamaChatProvider)
        assert isinstance(factory.get_embedding_provider(), OllamaEmbeddingProvider)

    def test_ollama_providers_satisfy_protocol(self) -> None:
        assert isinstance(OllamaChatProvider(), ChatProvider)
        assert isinstance(OllamaEmbeddingProvider(), EmbeddingProvider)

    def test_invalid_chat_provider_raises(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "chat_provider", "bogus")
        with pytest.raises(ValueError, match="chat_provider"):
            factory.get_chat_provider()

    def test_invalid_embedding_provider_raises(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "embedding_provider", "bogus")
        with pytest.raises(ValueError, match="embedding_provider"):
            factory.get_embedding_provider()


class TestClaudeSelection:
    def test_claude_without_key_raises_clearly(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "chat_provider", "claude")
        monkeypatch.setattr(settings, "claude_api_key", None)
        with pytest.raises(ValueError, match="CLAUDE_API_KEY"):
            factory.get_chat_provider()

    def test_key_not_logged(self, monkeypatch, caplog) -> None:
        monkeypatch.setattr(settings, "chat_provider", "claude")
        monkeypatch.setattr(settings, "claude_api_key", "sk-secret-xyz")
        factory._logged.clear()  # buộc log lại để kiểm tra nội dung
        with caplog.at_level(logging.INFO):
            provider = factory.get_chat_provider()
        from app.providers.claude import ClaudeChatProvider

        assert isinstance(provider, ClaudeChatProvider)
        assert "sk-secret-xyz" not in caplog.text  # KHÔNG lộ key
        assert "claude" in caplog.text.lower()  # có log tên provider


class TestOllamaEmbedding:
    @respx.mock
    async def test_embed_text_truncates_to_max_chars(self) -> None:
        captured = {}

        def _capture(request: httpx.Request) -> httpx.Response:
            import json

            captured["prompt"] = json.loads(request.content)["prompt"]
            return httpx.Response(200, json={"embedding": [0.1, 0.2, 0.3]})

        respx.post(f"{settings.ollama_base_url}/api/embeddings").mock(side_effect=_capture)

        long_text = "x" * (settings.max_embed_chars + 5000)
        result = await OllamaEmbeddingProvider().embed_text(long_text)

        assert result == [0.1, 0.2, 0.3]
        assert len(captured["prompt"]) == settings.max_embed_chars

    @respx.mock
    async def test_embed_text_retries_shorter_on_500(self) -> None:
        """Điều tiếng Việt dày đặc vượt token dù đã cắt ký tự → Ollama 500. Provider
        PHẢI thử lại với độ dài ngắn hơn để vẫn embed được (Pha 7)."""
        import json

        lengths: list[int] = []

        def _handler(request: httpx.Request) -> httpx.Response:
            n = len(json.loads(request.content)["prompt"])
            lengths.append(n)
            # Lần đầu (độ dài đầy đủ) trả 500; lần sau (ngắn hơn) trả 200.
            if n >= settings.max_embed_chars:
                return httpx.Response(500, json={"error": "input too long"})
            return httpx.Response(200, json={"embedding": [0.9]})

        respx.post(f"{settings.ollama_base_url}/api/embeddings").mock(side_effect=_handler)

        result = await OllamaEmbeddingProvider().embed_text("y" * (settings.max_embed_chars + 5000))

        assert result == [0.9]
        assert lengths[0] == settings.max_embed_chars  # thử độ dài đầy đủ trước
        assert lengths[-1] < settings.max_embed_chars  # rồi lùi ngắn hơn

    @respx.mock
    async def test_embed_text_raises_when_all_retries_fail(self) -> None:
        """Nếu mọi độ dài đều 500 → PHẢI raise (không nuốt lỗi)."""
        respx.post(f"{settings.ollama_base_url}/api/embeddings").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await OllamaEmbeddingProvider().embed_text("z" * (settings.max_embed_chars + 5000))

    @respx.mock
    async def test_embed_text_non_500_raises_immediately(self) -> None:
        """Lỗi khác 500 (vd 503 Ollama down) → raise ngay, KHÔNG retry ngắn hơn."""
        calls = {"n": 0}

        def _handler(request: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            return httpx.Response(503, json={"error": "unavailable"})

        respx.post(f"{settings.ollama_base_url}/api/embeddings").mock(side_effect=_handler)

        with pytest.raises(httpx.HTTPStatusError):
            await OllamaEmbeddingProvider().embed_text("w" * (settings.max_embed_chars + 5000))
        assert calls["n"] == 1  # không thử lại
