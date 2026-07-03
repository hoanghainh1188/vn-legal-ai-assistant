"""Search API endpoint — streams RAG results via SSE."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.schemas import SearchRequest
from app.services.rag import search_stream

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/query")
async def query_legal(request: SearchRequest) -> StreamingResponse:
    return StreamingResponse(
        search_stream(request.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
