"""OpenTelemetry tracing — auto-instrument FastAPI (Pha 4).

Exporter theo env chuẩn OTel (`OTEL_EXPORTER_OTLP_ENDPOINT`). Nếu vắng → tạo span
nhưng KHÔNG xuất (no-op) → chạy được ở dev không cần collector. Collector/Jaeger thật ở Pha 6.
"""

import logging
import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings

logger = logging.getLogger(__name__)


def setup_otel(app: FastAPI) -> None:
    provider = TracerProvider(resource=Resource.create({"service.name": settings.service_name}))

    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        logger.info("OTel: xuất trace qua OTLP")
    else:
        logger.info("OTel: không có OTLP endpoint → span no-op (dev)")

    trace.set_tracer_provider(provider)
    # instrument_app không đệm SSE (span kết thúc khi stream xong).
    FastAPIInstrumentor.instrument_app(app)
