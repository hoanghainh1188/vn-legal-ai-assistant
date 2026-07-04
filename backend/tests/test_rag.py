"""Tests for RAG pipeline (prompt + orchestration).

Truy hồi thuần (hybrid_rank) được test riêng ở test_vector_store.py. Ở đây test
orchestration dùng repository seam (không cần Postgres) + xử lý lỗi mid-stream.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.prompts.system import SYSTEM_PROMPT, build_prompt


class TestSystemPrompt:
    def test_system_prompt_contains_safety_clause(self) -> None:
        assert "tôi chưa tìm thấy quy định cụ thể" in SYSTEM_PROMPT

    def test_system_prompt_requires_citation(self) -> None:
        assert "Theo Điều" in SYSTEM_PROMPT

    def test_system_prompt_in_vietnamese(self) -> None:
        assert "trợ lý pháp lý" in SYSTEM_PROMPT

    def test_build_prompt_includes_context_and_query(self) -> None:
        prompt = build_prompt("Điều 8 content", "Việt kiều mua nhà?")
        assert "Điều 8 content" in prompt
        assert "Việt kiều mua nhà?" in prompt


def _patch_retrieval(mock_factory, mock_repository, mock_vs) -> None:
    """Cấu hình embedding + repository seam + hybrid_rank (rỗng) cho các test stream."""
    mock_factory.get_embedding_provider.return_value.embed_text = AsyncMock(return_value=[0.1, 0.2])
    repo = mock_repository.get_vector_repository.return_value
    repo.dense_candidates = AsyncMock(return_value=[])
    repo.all_rows = AsyncMock(return_value=[])
    mock_vs.hybrid_rank = MagicMock(return_value=[])


class TestSearchStreamMidStreamError:
    """FR-011: provider lỗi sau khi đã stream một phần → phát SSE 'error', không 'done'."""

    async def test_emits_error_event_no_done(self) -> None:
        class _FailProvider:
            async def stream(self, system_prompt, user_message):
                yield "phần "
                raise RuntimeError("boom giữa chừng")

        with (
            patch("app.services.rag.factory") as mock_factory,
            patch("app.services.rag.repository") as mock_repository,
            patch("app.services.rag.vector_store") as mock_vs,
        ):
            _patch_retrieval(mock_factory, mock_repository, mock_vs)
            mock_factory.get_chat_provider.return_value = _FailProvider()

            from app.services import rag

            events = [e async for e in rag.search_stream("câu hỏi")]

        types = [json.loads(e[len("data: ") :])["type"] for e in events]
        assert "token" in types  # đã stream một phần trước khi lỗi
        assert "error" in types  # có sự kiện error
        assert "done" not in types  # KHÔNG phát done


class TestSearchStreamCustomProvider:
    """US3 (Pha 0) vẫn đúng: một ChatProvider fake qua factory được rag dùng mà
    KHÔNG cần sửa orchestration."""

    async def test_uses_custom_chat_provider(self) -> None:
        class _FakeProvider:
            async def stream(self, system_prompt, user_message):
                yield "Câu "
                yield "trả lời"

        with (
            patch("app.services.rag.factory") as mock_factory,
            patch("app.services.rag.repository") as mock_repository,
            patch("app.services.rag.vector_store") as mock_vs,
        ):
            _patch_retrieval(mock_factory, mock_repository, mock_vs)
            mock_factory.get_chat_provider.return_value = _FakeProvider()

            from app.services import rag

            events = [e async for e in rag.search_stream("q")]

        parsed = [json.loads(e[len("data: ") :]) for e in events]
        tokens = "".join(p["data"] for p in parsed if p["type"] == "token")
        types = [p["type"] for p in parsed]
        assert tokens == "Câu trả lời"
        assert "done" in types
