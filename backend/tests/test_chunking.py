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


class TestDecreeStyleDocument:
    """Văn bản kiểu Nghị định/Thông tư (Pha 7): nhiều Chương, số điều duy nhất
    trong 1 văn bản — không trùng để tránh ghi đè khoá (document_id, article_number)."""

    _SAMPLE = """Chương I
QUY ĐỊNH CHUNG

Điều 1. Phạm vi điều chỉnh
Nghị định này quy định chi tiết một số điều của Luật Nhà ở.

Điều 2. Đối tượng áp dụng
Áp dụng với tổ chức, cá nhân liên quan.

Chương II
PHÁT TRIỂN NHÀ Ở XÃ HỘI

Điều 3. Điều kiện được mua nhà ở xã hội
1. Chưa có nhà ở thuộc sở hữu.
2. Thu nhập thuộc diện quy định.

Điều 4. Trình tự mua nhà ở xã hội
Thực hiện theo quy định tại Nghị định này."""

    def test_no_duplicate_article_numbers(self) -> None:
        chunks = chunk_legal_text(self._SAMPLE, "100/2024/ND-CP")
        nums = [c.article_number for c in chunks]
        assert nums == [1, 2, 3, 4]
        assert len(nums) == len(set(nums))  # không trùng số điều

    def test_chapters_across_document(self) -> None:
        chunks = chunk_legal_text(self._SAMPLE, "100/2024/ND-CP")
        assert chunks[0].chapter == "I"
        assert chunks[2].chapter == "II"  # Điều 3 thuộc Chương II

    def test_document_id_and_content(self) -> None:
        chunks = chunk_legal_text(self._SAMPLE, "100/2024/ND-CP")
        assert all(c.document_id == "100/2024/ND-CP" for c in chunks)
        assert "nhà ở xã hội" in chunks[2].content
