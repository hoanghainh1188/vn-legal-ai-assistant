"""Security headers (US2) — SSE không bị phá."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _fake_search(_query: str):
    async def gen():
        yield 'data: {"type": "done", "data": ""}\n\n'

    return gen()


class TestSecurityHeaders:
    def test_response_has_security_headers(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["x-frame-options"] == "DENY"
        assert "referrer-policy" in r.headers
        assert "permissions-policy" in r.headers

    def test_sse_still_streams_with_headers(self, client: TestClient) -> None:
        with patch("app.routers.query.search_stream", side_effect=_fake_search):
            r = client.post("/api/query", json={"query": "abc"})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        assert r.headers["x-content-type-options"] == "nosniff"  # header vẫn có trên SSE
