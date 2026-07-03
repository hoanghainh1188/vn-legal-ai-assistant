"""RAG orchestration — retrieve relevant chunks then stream LLM answer."""

import json
from collections.abc import AsyncIterator

from app.config import settings
from app.models.schemas import SourceDocument
from app.prompts.system import SYSTEM_PROMPT, build_prompt
from app.providers import factory
from app.services import vector_store


async def search_stream(query: str) -> AsyncIterator[str]:
    embedding_provider = factory.get_embedding_provider()
    query_embedding = await embedding_provider.embed_text(query)

    client = vector_store.get_client()
    collection = vector_store.get_collection(client)
    sources = vector_store.query_hybrid(
        collection, query_embedding, query, top_k=settings.retrieval_top_k
    )

    sources_event = {
        "type": "sources",
        "data": [s.model_dump() for s in sources],
    }
    yield f"data: {json.dumps(sources_event, ensure_ascii=False)}\n\n"

    context = _format_context(sources)
    user_message = build_prompt(context, query)

    chat_provider = factory.get_chat_provider()
    async for token in chat_provider.stream(SYSTEM_PROMPT, user_message):
        token_event = {"type": "token", "data": token}
        yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"

    done_event = {"type": "done", "data": ""}
    yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"


def _format_context(sources: list[SourceDocument]) -> str:
    parts: list[str] = []
    for s in sources:
        parts.append(f"--- {s.document_id}, Điều {s.article_number}: {s.article_title} ---")
        parts.append(s.content)
        parts.append("")
    return "\n".join(parts)
