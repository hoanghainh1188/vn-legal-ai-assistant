"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.connection import close_pool
from app.routers.query import router as query_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Đóng pool Postgres gọn gàng khi shutdown (tránh cảnh báo unclosed connection).
    await close_pool()


app = FastAPI(
    title="VN Legal AI Assistant",
    description="RAG-powered Vietnamese Housing Law search",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(query_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
