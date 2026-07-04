"""Unit tests cho hàm thuần hybrid_rank — KHÔNG cần Postgres.

Bảo toàn hành vi hybrid của PoC: dense (vector) + lexical (BM25-lite, title×3) +
RRF + guarantee-slot đưa điều khớp tiêu đề (Điều 58) lên dù dense rank thấp.
"""

from app.db.repository import RetrievedRow
from app.services.vector_store import hybrid_rank


def _corpus() -> list[RetrievedRow]:
    return [
        RetrievedRow("a", 1, "Sở hữu nhà ở", "doc", "I", "Nội dung về sở hữu.", [1.0, 0.0]),
        RetrievedRow("b", 2, "Giao dịch nhà ở", "doc", "II", "Nội dung về giao dịch.", [0.9, 0.1]),
        RetrievedRow(
            "target", 58, "Thời hạn chung cư", "doc", "IV", "Nội dung về thời hạn.", [0.0, 1.0]
        ),
    ]


class TestHybridRank:
    def test_lexical_match_surfaces_low_dense_rank(self) -> None:
        corpus = _corpus()
        # Dense xếp điều khớp từ khoá (target) CUỐI cùng — mô phỏng bge dưới-xếp-hạng.
        dense = [corpus[0], corpus[1], corpus[2]]
        results = hybrid_rank(
            query_embedding=[1.0, 0.0],
            query_text="thời hạn chung cư bao nhiêu năm",
            dense=dense,
            corpus=corpus,
            top_k=2,
        )
        assert 58 in {r.article_number for r in results}

    def test_guarantee_slot_surfaces_article_absent_from_dense(self) -> None:
        # Case gắt nhất (SC-002): điều khớp tiêu đề (Điều 58) HOÀN TOÀN vắng khỏi
        # dense pool → chỉ guarantee-slot (reserved = top_k//2 - 1) mới đưa nó vào.
        corpus = _corpus()
        dense = [corpus[0], corpus[1]]  # target (58) KHÔNG có trong dense
        results = hybrid_rank(
            query_embedding=[1.0, 0.0],
            query_text="thời hạn chung cư bao nhiêu năm",
            dense=dense,
            corpus=corpus,
            top_k=8,  # reserved = 8//2 - 1 = 3 slot cho lexical top
        )
        assert 58 in {r.article_number for r in results}

    def test_empty_corpus_returns_empty(self) -> None:
        assert (
            hybrid_rank(
                query_embedding=[0.1, 0.2],
                query_text="bất kỳ",
                dense=[],
                corpus=[],
                top_k=5,
            )
            == []
        )

    def test_returns_source_documents_sorted_by_relevance(self) -> None:
        corpus = _corpus()
        results = hybrid_rank(
            query_embedding=[1.0, 0.0],
            query_text="sở hữu nhà ở",
            dense=corpus,
            corpus=corpus,
            top_k=3,
        )
        assert results
        scores = [r.relevance_score for r in results]
        assert scores == sorted(scores, reverse=True)
        # Trả về đúng cấu trúc SourceDocument (không có field chapter — không đổi hợp đồng).
        assert results[0].article_number in {1, 2, 58}
