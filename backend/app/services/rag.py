"""RAG orchestration — retrieve relevant chunks then stream LLM answer."""

import json
import logging
from collections.abc import AsyncIterator

from app.config import settings
from app.db import repository
from app.models.schemas import SourceDocument
from app.prompts.system import SYSTEM_PROMPT, build_prompt
from app.providers import factory
from app.services import vector_store

logger = logging.getLogger(__name__)


async def search_stream(query: str) -> AsyncIterator[str]:
    embedding_provider = factory.get_embedding_provider()
    query_embedding = await embedding_provider.embed_text(query)

    repo = repository.get_vector_repository()
    dense = await repo.dense_candidates(query_embedding, settings.vector_pool)
    corpus = await repo.all_rows()
    sources = vector_store.hybrid_rank(
        query_embedding, query, dense, corpus, top_k=settings.retrieval_top_k
    )

    sources_event = {
        "type": "sources",
        "data": [s.model_dump() for s in sources],
    }
    yield f"data: {json.dumps(sources_event, ensure_ascii=False)}\n\n"

    context = _format_context(sources)
    user_message = build_prompt(context, query)

    chat_provider = factory.get_chat_provider()
    try:
        async for token in chat_provider.stream(SYSTEM_PROMPT, user_message):
            token_event = {"type": "token", "data": token}
            yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"
    except Exception:
        # Lỗi giữa chừng stream (FR-011): phát sự kiện 'error' và dừng — KHÔNG
        # phát 'done' để client không coi phần dở là câu trả lời hoàn chỉnh.
        # Không lộ chi tiết lỗi nhạy cảm cho người dùng.
        logger.exception("Lỗi khi streaming câu trả lời từ chat provider")
        error_event = {
            "type": "error",
            "data": "Đã xảy ra lỗi khi tạo câu trả lời. Vui lòng thử lại.",
        }
        yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        return

    done_event = {"type": "done", "data": ""}
    yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"


def _format_context(sources: list[SourceDocument]) -> str:
    parts: list[str] = []
    for s in sources:
        parts.append(f"--- {s.document_id}, Điều {s.article_number}: {s.article_title} ---")
        parts.append(s.content)
        parts.append("")
    return "\n".join(parts)
