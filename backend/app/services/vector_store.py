"""ChromaDB vector store operations."""

import math
import re

import chromadb

from app.config import settings
from app.models.schemas import LegalChunk, SourceDocument

# Common Vietnamese function words that carry little retrieval signal.
_STOPWORDS = {
    "có", "và", "của", "là", "được", "cho", "các", "một", "này", "đó", "khi",
    "về", "theo", "trong", "tại", "bao", "nhiêu", "tối", "đa", "không", "với",
    "thì", "mà", "hay", "hoặc", "những", "đến", "từ", "ra", "vào", "phải",
    "sẽ", "đã", "bị", "như", "để", "nếu", "còn", "gì", "ai", "nào", "thế",
}


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"\w+", text.lower(), flags=re.UNICODE) if len(w) > 1]


def _keyword_terms(query: str) -> list[str]:
    return [w for w in _tokens(query) if w not in _STOPWORDS]


def get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    return client.get_or_create_collection(
        name=settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(
    collection: chromadb.Collection,
    chunks: list[LegalChunk],
    embeddings: list[list[float]],
) -> None:
    collection.upsert(
        ids=[f"{c.document_id}__dieu_{c.article_number}" for c in chunks],
        documents=[c.content for c in chunks],
        embeddings=embeddings,
        metadatas=[
            {
                "article_number": c.article_number,
                "article_title": c.article_title,
                "document_id": c.document_id,
                "chapter": c.chapter,
            }
            for c in chunks
        ],
    )


def query_similar(
    collection: chromadb.Collection,
    query_embedding: list[float],
    top_k: int = 3,
) -> list[SourceDocument]:
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    documents: list[SourceDocument] = []
    if not results["documents"] or not results["documents"][0]:
        return documents

    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
        strict=True,
    ):
        documents.append(
            SourceDocument(
                article_number=meta["article_number"],
                article_title=meta["article_title"],
                document_id=meta["document_id"],
                content=doc,
                relevance_score=round(1 - distance, 4),
            )
        )

    return documents


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def query_hybrid(
    collection: chromadb.Collection,
    query_embedding: list[float],
    query_text: str,
    top_k: int = 8,
    vector_pool: int = 30,
    rrf_k: int = 60,
) -> list[SourceDocument]:
    """Hybrid retrieval: fuse dense (vector) and lexical (keyword) rankings.

    nomic-embed-text alone under-ranks Vietnamese articles when the query
    wording differs from the article's (e.g. "sở hữu" vs "sử dụng"). A keyword
    pass over titles/content recovers those, and Reciprocal Rank Fusion merges
    both rankings robustly without tuning weights.
    """
    everything = collection.get(include=["documents", "metadatas", "embeddings"])
    ids = everything["ids"]
    if not ids:
        return []

    docs = everything["documents"]
    metas = everything["metadatas"]
    embeddings = everything["embeddings"]
    by_id = {
        cid: (doc, meta, emb)
        for cid, doc, meta, emb in zip(ids, docs, metas, embeddings, strict=True)
    }

    # Dense ranking from ChromaDB.
    vector_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(vector_pool, len(ids)),
        include=["distances"],
    )
    vector_order = vector_results["ids"][0] if vector_results["ids"] else []

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
        for cid, (doc, meta, _emb) in by_id.items():
            title_of[cid] = str(meta.get("article_title", "")).lower()
            body_of[cid] = doc.lower()
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

    # Guarantee the strongest lexical (title keyword) matches are always
    # present: the dense model under-ranks Vietnamese articles whose wording
    # differs from the query, but a title match is a highly reliable signal.
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
        doc, meta, emb = by_id[cid]
        documents.append(
            SourceDocument(
                article_number=meta["article_number"],
                article_title=meta["article_title"],
                document_id=meta["document_id"],
                content=doc,
                relevance_score=round(_cosine(query_embedding, emb), 4),
            )
        )
    # Present most semantically relevant first — leads both the "Cơ sở pháp lý"
    # display and the LLM context with the strongest match.
    documents.sort(key=lambda d: d.relevance_score, reverse=True)
    return documents
