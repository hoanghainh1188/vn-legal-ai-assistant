"""Search API endpoint — streams RAG results via SSE."""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.db import repository
from app.models.schemas import SearchRequest
from app.observability.ratelimit import limiter, rate_limit_value
from app.services.rag import search_stream

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/query")
@limiter.limit(rate_limit_value)
async def query_legal(request: Request, payload: SearchRequest) -> StreamingResponse:
    # Rate-limit kiểm TRƯỚC khi vào đây (slowapi decorator) → SSE-safe, không đệm stream.
    return StreamingResponse(
        search_stream(payload.query, payload.domain),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/domains")
async def list_domains() -> dict[str, list[str]]:
    """Danh sách lĩnh vực đang có (động) — UI populate bộ lọc. Không bị rate-limit."""
    domains = await repository.get_vector_repository().list_domains()
    return {"domains": domains}
