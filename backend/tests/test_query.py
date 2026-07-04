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
    def test_query_returns_sse_stream(self, mock_search: AsyncMock, client: TestClient) -> None:
        async def fake_stream(query: str, domain=None):
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

    @patch("app.routers.query.search_stream")
    def test_query_accepts_domain_filter(self, mock_search: AsyncMock, client: TestClient) -> None:
        # Feature #8: /api/query nhận tham số domain tùy chọn.
        async def fake_stream(query: str, domain=None):
            yield 'data: {"type": "done", "data": ""}\n\n'

        mock_search.side_effect = fake_stream
        response = client.post("/api/query", json={"query": "abc", "domain": "Nhà ở"})
        assert response.status_code == 200
        # search_stream được gọi kèm domain đã chọn.
        assert mock_search.call_args.args[1] == "Nhà ở"


class TestDomainsEndpoint:
    @patch("app.routers.query.repository.get_vector_repository")
    def test_domains_returns_list(self, mock_repo, client: TestClient) -> None:
        mock_repo.return_value.list_domains = AsyncMock(return_value=["Nhà ở"])
        response = client.get("/api/domains")
        assert response.status_code == 200
        assert response.json() == {"domains": ["Nhà ở"]}
