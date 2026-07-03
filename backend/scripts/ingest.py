"""One-command ingestion: source HTML → clean text → chunk → embed → ChromaDB.

Runs the whole corpus declared in `sources.py`. Idempotent — resets the
collection first, then rebuilds. If a source's HTML is present it is
re-parsed into `data/raw/*.txt`; otherwise the existing .txt is used.

    uv run python scripts/ingest.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.models.schemas import LegalChunk as AppChunk
from app.services import llm, vector_store
from scripts.chunk_legal_text import chunk_legal_text
from scripts.fetch_sources import ensure_html
from scripts.html_to_legal_text import html_to_legal_text
from scripts.sources import SOURCES, LegalSource

BASE = Path(__file__).resolve().parent.parent
RAW_TEXT = BASE / "data" / "raw"


def build_text(source: LegalSource) -> str:
    """Turn a source into clean legal text: fetch its HTML from the MOJ API if
    not already cached, parse it, and write the .txt."""
    html_path = ensure_html(source)  # fetches from API on cache miss
    text = html_to_legal_text(html_path.read_text(encoding="utf-8"))
    (RAW_TEXT / source.text).write_text(text, encoding="utf-8")
    return text


async def ingest_source(
    source: LegalSource, collection: vector_store.chromadb.Collection
) -> int:
    print(f"• {source.name} ({source.document_id})")
    text = build_text(source)
    chunks = chunk_legal_text(text, source.document_id)
    print(f"    parsed {len(chunks)} articles, embedding ...")

    embeddings = await llm.embed_texts([c.content for c in chunks])
    app_chunks = [
        AppChunk(
            article_number=c.article_number,
            article_title=c.article_title,
            document_id=c.document_id,
            chapter=c.chapter,
            content=c.content,
        )
        for c in chunks
    ]
    vector_store.add_chunks(collection, app_chunks, embeddings)
    print(f"    stored {len(chunks)} chunks")
    return len(chunks)


async def main() -> None:
    client = vector_store.get_client()
    # Reset for a clean, reproducible rebuild (also handles embedding-dim changes).
    try:
        client.delete_collection(settings.collection_name)
    except Exception:
        pass
    collection = vector_store.get_collection(client)

    total = 0
    for source in SOURCES:
        total += await ingest_source(source, collection)

    print(f"\nIngestion complete — {total} chunks from {len(SOURCES)} documents.")


if __name__ == "__main__":
    asyncio.run(main())
