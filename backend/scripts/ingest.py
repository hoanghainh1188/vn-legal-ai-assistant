"""One-command ingestion: source HTML → clean text → chunk → embed → Postgres+pgvector.

Runs the whole corpus declared in `sources.py`. Idempotent — upsert theo khoá
(document_id, article_number), chạy lại không nhân bản. Bảng `legal_chunks` do
Supabase migrations tạo (`supabase db reset`). Nếu HTML của một nguồn có sẵn thì
re-parse vào `data/raw/*.txt`; nếu không thì dùng .txt hiện có.

    uv run python scripts/ingest.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import repository
from app.db.connection import close_pool
from app.db.repository import ChunkRow
from app.providers import factory
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


async def ingest_source(source: LegalSource, repo: repository.VectorRepository) -> int:
    print(f"• {source.name} ({source.document_id})")
    text = build_text(source)
    chunks = chunk_legal_text(text, source.document_id)
    print(f"    parsed {len(chunks)} articles, embedding ...")

    embeddings = await factory.get_embedding_provider().embed_texts([c.content for c in chunks])
    rows = [
        ChunkRow(
            article_number=c.article_number,
            article_title=c.article_title,
            document_id=c.document_id,
            chapter=c.chapter,
            content=c.content,
            document_name=source.name,
            eff_status=source.eff_status,
            eff_date=source.eff_date,
        )
        for c in chunks
    ]
    await repo.upsert_chunks(rows, embeddings)
    print(f"    stored {len(chunks)} chunks")
    return len(chunks)


async def main() -> None:
    # Schema (legal_chunks) do Supabase migrations tạo — chạy `supabase db reset` trước.
    repo = repository.get_vector_repository()

    total = 0
    for source in SOURCES:
        total += await ingest_source(source, repo)

    await close_pool()
    print(f"\nIngestion complete — {total} chunks from {len(SOURCES)} documents.")


if __name__ == "__main__":
    asyncio.run(main())
