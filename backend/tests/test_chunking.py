"""Tests for Vietnamese legal text chunker."""

import pytest

from scripts.chunk_legal_text import chunk_legal_text


class TestChunkLegalText:
    def test_splits_by_article_boundaries(self, sample_legal_text: str) -> None:
        chunks = chunk_legal_text(sample_legal_text, "test-doc")
        assert len(chunks) == 4
        assert chunks[0].article_number == 1
        assert chunks[1].article_number == 2
        assert chunks[2].article_number == 8
        assert chunks[3].article_number == 9

    def test_extracts_article_title(self, sample_legal_text: str) -> None:
        chunks = chunk_legal_text(sample_legal_text, "test-doc")
        assert chunks[0].article_title == "Phạm vi điều chỉnh"
        assert chunks[2].article_title == "Đối tượng được sở hữu nhà ở"

    def test_assigns_document_id(self, sample_legal_text: str) -> None:
        chunks = chunk_legal_text(sample_legal_text, "27/2023/QH15")
        for chunk in chunks:
            assert chunk.document_id == "27/2023/QH15"

    def test_detects_chapter(self, sample_legal_text: str) -> None:
        chunks = chunk_legal_text(sample_legal_text, "test-doc")
        assert chunks[0].chapter == "I"
        assert chunks[1].chapter == "I"
        assert chunks[2].chapter == "II"
        assert chunks[3].chapter == "II"

    def test_preserves_full_content(self, sample_legal_text: str) -> None:
        chunks = chunk_legal_text(sample_legal_text, "test-doc")
        assert "Tổ chức, hộ gia đình, cá nhân trong nước" in chunks[2].content
        assert "Điều 8." in chunks[2].content

    def test_empty_text_returns_empty_list(self) -> None:
        chunks = chunk_legal_text("", "test-doc")
        assert chunks == []

    def test_no_articles_returns_empty_list(self) -> None:
        chunks = chunk_legal_text("Some random text without articles", "test-doc")
        assert chunks == []

    def test_single_article(self) -> None:
        text = "Điều 1. Phạm vi\nNội dung điều 1."
        chunks = chunk_legal_text(text, "test")
        assert len(chunks) == 1
        assert chunks[0].article_number == 1
        assert "Nội dung điều 1" in chunks[0].content

    def test_vietnamese_diacritics_preserved(self, sample_legal_text: str) -> None:
        chunks = chunk_legal_text(sample_legal_text, "test-doc")
        assert "Điều" in chunks[0].content
        assert "sở hữu" in chunks[2].content
        assert "Việt Nam" in chunks[3].content

    def test_chunks_are_immutable(self, sample_legal_text: str) -> None:
        chunks = chunk_legal_text(sample_legal_text, "test-doc")
        with pytest.raises(AttributeError):
            chunks[0].article_number = 99  # type: ignore[misc]
