"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.db.connection import close_pool
from app.observability.logging_config import configure_logging
from app.observability.middleware import RequestContextMiddleware
from app.observability.otel import setup_otel
from app.observability.ratelimit import limiter, rate_limit_handler
from app.observability.security import SecurityHeadersMiddleware
from app.routers.query import router as query_router

configure_logging()


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

# Rate-limit (slowapi): decorator ở /api/query + handler 429. /health, /metrics miễn.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Middleware (cái add sau bọc ngoài). Sau setup_otel/Prometheus (cuối file), thứ tự thực
# tế: OTel → Prometheus → RequestContext → SecurityHeaders → CORS → app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

app.include_router(query_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Observability: traces (OTel) + metrics (/metrics cho Prometheus).
setup_otel(app)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
