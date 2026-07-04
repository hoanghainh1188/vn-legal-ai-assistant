"""Structured JSON logging + request-id contextvar (Pha 4).

Mọi log trong 1 request tự kèm request_id (qua contextvar). KHÔNG log secret/PII
(không log toàn văn câu hỏi/email/khoá) — Constitution V.
"""

import logging
from contextvars import ContextVar

from pythonjsonlogger.json import JsonFormatter  # python-json-logger >= 3.0

from app.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get()
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler()
    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s",
        rename_fields={"asctime": "ts", "levelname": "level", "name": "logger"},
    )
    handler.setFormatter(formatter)
    handler.addFilter(_RequestIdFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())
