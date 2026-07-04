"""Test ClaudeChatProvider streaming (mock Anthropic SDK — không cần key/mạng)."""

from unittest.mock import patch

from app.config import settings


class _FakeStreamCtx:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    async def __aenter__(self) -> "_FakeStreamCtx":
        return self

    async def __aexit__(self, *args) -> bool:
        return False

    @property
    def text_stream(self):
        async def _gen():
            for c in self._chunks:
                yield c

        return _gen()


class _FakeMessages:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    def stream(self, **kwargs) -> _FakeStreamCtx:
        return _FakeStreamCtx(self._chunks)


class _FakeAnthropic:
    def __init__(self, chunks: list[str]) -> None:
        self.messages = _FakeMessages(chunks)


class TestClaudeChatProvider:
    async def test_stream_yields_only_text(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "claude_api_key", "sk-test-key")
        with patch("app.providers.claude.AsyncAnthropic") as mock_cls:
            mock_cls.return_value = _FakeAnthropic(["Xin ", "chào ", "bạn"])
            from app.providers.claude import ClaudeChatProvider

            provider = ClaudeChatProvider()
            out = [t async for t in provider.stream("system", "câu hỏi")]

        assert out == ["Xin ", "chào ", "bạn"]

    def test_init_requires_key(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "claude_api_key", None)
        import pytest

        from app.providers.claude import ClaudeChatProvider

        with pytest.raises(ValueError, match="claude_api_key"):
            ClaudeChatProvider()
