"""Rate-limit /api/query (US1). SSE-safe: 429 trước khi stream."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.observability.ratelimit import limiter


def _reset_limiter() -> None:
    reset = getattr(limiter, "reset", None)
    if callable(reset):
        try:
            reset()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def _clean_limiter():
    _reset_limiter()
    yield
    _reset_limiter()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _fake_search(_query: str, _domain=None):
    async def gen():
        yield 'data: {"type": "done", "data": ""}\n\n'

    return gen()


class TestRateLimit:
    def test_exceeding_limit_returns_429(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(settings, "rate_limit", "3/minute")
        with patch("app.routers.query.search_stream", side_effect=_fake_search):
            codes = [client.post("/api/query", json={"query": "abc"}).status_code for _ in range(4)]
        assert codes[:3] == [200, 200, 200]
        assert codes[3] == 429

    def test_health_not_rate_limited(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(settings, "rate_limit", "2/minute")
        codes = [client.get("/health").status_code for _ in range(5)]
        assert all(c == 200 for c in codes)

    def test_metrics_not_rate_limited(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(settings, "rate_limit", "2/minute")
        codes = [client.get("/metrics").status_code for _ in range(5)]
        assert all(c == 200 for c in codes)
