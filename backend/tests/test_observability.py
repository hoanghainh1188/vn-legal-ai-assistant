"""Observability (US3): request-id, structured log (no-PII), /metrics Prometheus."""

import logging
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


class TestObservability:
    def test_response_has_request_id(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.headers.get("x-request-id")

    def test_metrics_prometheus_format(self, client: TestClient) -> None:
        r = client.get("/metrics")
        assert r.status_code == 200
        assert "# HELP" in r.text or "# TYPE" in r.text

    def test_request_logged_structured_no_pii(self, client: TestClient, caplog) -> None:
        secret_query = "CAUHOIBIMAT_XYZ_123"
        with caplog.at_level(logging.INFO, logger="app.request"):
            with patch("app.routers.query.search_stream", side_effect=_fake_search):
                client.post("/api/query", json={"query": secret_query})

        records = [r for r in caplog.records if r.name == "app.request"]
        assert records, "phải có bản ghi log cho request"
        rec = records[-1]
        assert getattr(rec, "path", None) == "/api/query"
        assert getattr(rec, "status_code", None) == 200
        assert hasattr(rec, "duration_ms")
        assert getattr(rec, "request_id", None)
        # trace_id có mặt để tương quan log ↔ trace (FR-014); là hex 32 khi có span.
        assert hasattr(rec, "trace_id")
        if rec.trace_id is not None:
            assert len(rec.trace_id) == 32

        # no-PII: toàn văn câu hỏi KHÔNG xuất hiện trong message HAY bất kỳ field nào của record.
        for r in caplog.records:
            assert secret_query not in r.getMessage()
            assert secret_query not in str(vars(r))
