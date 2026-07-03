"""Tests for RAG pipeline and vector store."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.schemas import SourceDocument
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
                            {"article_number": 8, "article_title": "Title 8", "document_id": "doc1"},
                            {"article_number": 9, "article_title": "Title 9", "document_id": "doc1"},
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
                {"article_number": 58, "article_title": "Thời hạn sử dụng nhà chung cư", "document_id": "doc"},
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
            return {"ids": [["a", "b", "target"][:n_results]], "distances": [[0.1, 0.2, 0.9][:n_results]]}

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
