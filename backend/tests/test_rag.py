"""Tests for RAG pipeline and vector store."""

import json
from unittest.mock import AsyncMock, patch

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


class TestVectorStore:
    def test_query_similar_returns_source_documents(self) -> None:
        from app.services.vector_store import query_similar

        class FakeCollection:
            def query(self, **kwargs):
                return {
                    "documents": [["content 1", "content 2"]],
                    "metadatas": [
                        [
                            {"article_number": 8, "article_title": "T8", "document_id": "doc1"},
                            {"article_number": 9, "article_title": "T9", "document_id": "doc1"},
                        ]
                    ],
                    "distances": [[0.1, 0.2]],
                }

        results = query_similar(FakeCollection(), [0.1] * 768, top_k=2)
        assert len(results) == 2
        assert results[0].article_number == 8
        assert results[0].relevance_score == 0.9
        assert results[1].article_number == 9

    def test_query_similar_empty_results(self) -> None:
        from app.services.vector_store import query_similar

        class FakeCollection:
            def query(self, **kwargs):
                return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        results = query_similar(FakeCollection(), [0.1] * 768)
        assert results == []


class TestHybridRetrieval:
    """The dense model may under-rank a title-matching article; the lexical
    guarantee must still surface it."""

    class FakeCollection:
        def __init__(self) -> None:
            self._ids = ["a", "b", "target"]
            self._docs = [
                "Nội dung về sở hữu.",
                "Nội dung về giao dịch.",
                "Nội dung về thời hạn.",
            ]
            self._metas = [
                {"article_number": 1, "article_title": "Sở hữu nhà ở", "document_id": "doc"},
                {"article_number": 2, "article_title": "Giao dịch nhà ở", "document_id": "doc"},
                {"article_number": 58, "article_title": "Thời hạn chung cư", "document_id": "doc"},
            ]
            self._embs = [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]]

        def get(self, include=None):
            return {
                "ids": self._ids,
                "documents": self._docs,
                "metadatas": self._metas,
                "embeddings": self._embs,
            }

        def query(self, query_embeddings=None, n_results=None, include=None):
            # Dense ranking favours a/b, ranks the keyword target last.
            ids = ["a", "b", "target"][:n_results]
            dist = [0.1, 0.2, 0.9][:n_results]
            return {"ids": [ids], "distances": [dist]}

    def test_lexical_match_surfaces_low_dense_rank(self) -> None:
        from app.services.vector_store import query_hybrid

        results = query_hybrid(
            self.FakeCollection(),
            query_embedding=[1.0, 0.0],
            query_text="thời hạn chung cư bao nhiêu năm",
            top_k=2,
        )
        surfaced = {r.article_number for r in results}
        assert 58 in surfaced

    def test_empty_collection_returns_empty(self) -> None:
        from app.services.vector_store import query_hybrid

        class Empty:
            def get(self, include=None):
                return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}

        assert query_hybrid(Empty(), [0.1, 0.2], "bất kỳ", top_k=5) == []


class TestSearchStreamMidStreamError:
    """FR-011: provider lỗi sau khi đã stream một phần → phát SSE 'error', không 'done'."""

    async def test_emits_error_event_no_done(self) -> None:
        class _FailProvider:
            async def stream(self, system_prompt, user_message):
                yield "phần "
                raise RuntimeError("boom giữa chừng")

        with (
            patch("app.services.rag.factory") as mock_factory,
            patch("app.services.rag.vector_store") as mock_vs,
        ):
            emb = mock_factory.get_embedding_provider.return_value
            emb.embed_text = AsyncMock(return_value=[0.1, 0.2])
            mock_vs.get_client.return_value = object()
            mock_vs.get_collection.return_value = object()
            mock_vs.query_hybrid.return_value = []
            mock_factory.get_chat_provider.return_value = _FailProvider()

            from app.services import rag

            events = [e async for e in rag.search_stream("câu hỏi")]

        types = [json.loads(e[len("data: "):])["type"] for e in events]
        assert "token" in types  # đã stream một phần trước khi lỗi
        assert "error" in types  # có sự kiện error
        assert "done" not in types  # KHÔNG phát done


class TestSearchStreamCustomProvider:
    """US3: một ChatProvider mới (fake) qua factory được rag dùng mà KHÔNG cần
    sửa mã orchestration."""

    async def test_uses_custom_chat_provider(self) -> None:
        class _FakeProvider:
            async def stream(self, system_prompt, user_message):
                yield "Câu "
                yield "trả lời"

        with (
            patch("app.services.rag.factory") as mock_factory,
            patch("app.services.rag.vector_store") as mock_vs,
        ):
            mock_factory.get_embedding_provider.return_value.embed_text = AsyncMock(
                return_value=[0.1]
            )
            mock_vs.get_client.return_value = object()
            mock_vs.get_collection.return_value = object()
            mock_vs.query_hybrid.return_value = []
            mock_factory.get_chat_provider.return_value = _FakeProvider()

            from app.services import rag

            events = [e async for e in rag.search_stream("q")]

        parsed = [json.loads(e[len("data: "):]) for e in events]
        tokens = "".join(p["data"] for p in parsed if p["type"] == "token")
        types = [p["type"] for p in parsed]
        assert tokens == "Câu trả lời"
        assert "done" in types
