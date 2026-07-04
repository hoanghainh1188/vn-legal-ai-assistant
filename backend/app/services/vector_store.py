"""Hybrid retrieval — hàm THUẦN trên rows (không phụ thuộc kho lưu trữ).

Tầng dữ liệu (Postgres+pgvector) nằm ở `app.db.repository`; ở đây chỉ hợp nhất
dense + lexical rồi dựng `SourceDocument`. Thuần → test được không cần DB.
"""

import math
import re

from app.db.repository import RetrievedRow
from app.models.schemas import SourceDocument

# Common Vietnamese function words that carry little retrieval signal.
_STOPWORDS = {
    "có",
    "và",
    "của",
    "là",
    "được",
    "cho",
    "các",
    "một",
    "này",
    "đó",
    "khi",
    "về",
    "theo",
    "trong",
    "tại",
    "bao",
    "nhiêu",
    "tối",
    "đa",
    "không",
    "với",
    "thì",
    "mà",
    "hay",
    "hoặc",
    "những",
    "đến",
    "từ",
    "ra",
    "vào",
    "phải",
    "sẽ",
    "đã",
    "bị",
    "như",
    "để",
    "nếu",
    "còn",
    "gì",
    "ai",
    "nào",
    "thế",
}


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"\w+", text.lower(), flags=re.UNICODE) if len(w) > 1]


def _keyword_terms(query: str) -> list[str]:
    return [w for w in _tokens(query) if w not in _STOPWORDS]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def hybrid_rank(
    query_embedding: list[float],
    query_text: str,
    dense: list[RetrievedRow],
    corpus: list[RetrievedRow],
    top_k: int = 8,
    rrf_k: int = 60,
) -> list[SourceDocument]:
    """Hợp nhất dense (vector) và lexical (keyword) rankings.

    bge-m3 vẫn có thể dưới-xếp-hạng điều luật khi câu hỏi dùng từ khác với điều
    (vd "sở hữu" vs "sử dụng"). Một lượt keyword trên tiêu đề/nội dung khôi phục
    chúng, và Reciprocal Rank Fusion hợp nhất hai bảng xếp hạng mà không cần chỉnh
    trọng số.

    - ``dense``: ứng viên theo cosine (đã sắp), lấy thứ tự dense.
    - ``corpus``: toàn bộ rows (để tính IDF/lexical + tra cứu theo id).
    """
    by_id = {row.id: row for row in corpus}
    if not by_id:
        return []

    vector_order = [row.id for row in dense]

    # Lexical ranking (BM25-lite): IDF-weight terms so a discriminative match
    # like "chung cư" counts far more than ubiquitous words like "sở"/"hữu",
    # and weight title hits above body hits.
    terms = _keyword_terms(query_text)
    lexical_scores: dict[str, float] = {}
    if terms:
        total = len(by_id)
        doc_freq: dict[str, int] = {}
        title_of: dict[str, str] = {}
        body_of: dict[str, str] = {}
        for cid, row in by_id.items():
            title_of[cid] = row.article_title.lower()
            body_of[cid] = row.content.lower()
            haystack = title_of[cid] + " " + body_of[cid]
            for t in set(terms):
                if t in haystack:
                    doc_freq[t] = doc_freq.get(t, 0) + 1
        idf = {
            t: math.log(1 + (total - doc_freq.get(t, 0) + 0.5) / (doc_freq.get(t, 0) + 0.5))
            for t in set(terms)
        }
        for cid in by_id:
            score = 0.0
            for t in set(terms):
                if t in title_of[cid]:
                    score += 3 * idf[t]
                elif t in body_of[cid]:
                    score += idf[t]
            if score:
                lexical_scores[cid] = score
    lexical_order = sorted(lexical_scores, key=lexical_scores.get, reverse=True)

    # Reciprocal Rank Fusion.
    fused: dict[str, float] = {}
    for rank, cid in enumerate(vector_order):
        fused[cid] = fused.get(cid, 0.0) + 1.0 / (rrf_k + rank)
    for rank, cid in enumerate(lexical_order):
        fused[cid] = fused.get(cid, 0.0) + 1.0 / (rrf_k + rank)

    fused_order = sorted(fused, key=fused.get, reverse=True)

    # Guarantee the strongest lexical (title keyword) matches are always present:
    # the dense model under-ranks Vietnamese articles whose wording differs from
    # the query, but a title match is a highly reliable signal.
    reserved = max(0, top_k // 2 - 1)
    lexical_top = lexical_order[:reserved]
    top_ids: list[str] = []
    for cid in lexical_top + fused_order:
        if cid not in top_ids:
            top_ids.append(cid)
        if len(top_ids) >= top_k:
            break

    documents: list[SourceDocument] = []
    for cid in top_ids:
        row = by_id[cid]
        documents.append(
            SourceDocument(
                article_number=row.article_number,
                article_title=row.article_title,
                document_id=row.document_id,
                content=row.content,
                relevance_score=round(_cosine(query_embedding, row.embedding), 4),
            )
        )
    # Present most semantically relevant first — leads both the "Cơ sở pháp lý"
    # display and the LLM context with the strongest match.
    documents.sort(key=lambda d: d.relevance_score, reverse=True)
    return documents
