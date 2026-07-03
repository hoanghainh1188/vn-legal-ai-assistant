"""Tests for the search API endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestQueryEndpoint:
    @patch("app.routers.query.search_stream")
    def test_query_returns_sse_stream(
        self, mock_search: AsyncMock, client: TestClient
    ) -> None:
        async def fake_stream(query: str):
            yield 'data: {"type": "sources", "data": []}\n\n'
            yield 'data: {"type": "token", "data": "Hello"}\n\n'
            yield 'data: {"type": "done", "data": ""}\n\n'

        mock_search.return_value = fake_stream("test")

        response = client.post(
            "/api/query",
            json={"query": "test question"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

    def test_query_rejects_empty_query(self, client: TestClient) -> None:
        response = client.post("/api/query", json={"query": ""})
        assert response.status_code == 422

    def test_query_rejects_missing_query(self, client: TestClient) -> None:
        response = client.post("/api/query", json={})
        assert response.status_code == 422
