"""Slice 14: Structured JSON logging with secret masking.

Usage:
    from marketmind.logging_config import setup_logging, get_logger

    setup_logging()                     # call once at app startup
    log = get_logger(__name__)
    log.info("scored product", extra={"product": "Kit", "score": 0.72})

Secret masking: any string value in a log record matching a known secret
pattern (sk_, pk_, whsec_, shpat_, Bearer) is replaced with ***REDACTED***.
The masker is applied at the Formatter level so it covers all handlers.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any

_SECRET_PATTERN = re.compile(
    r"(sk_(?:live|test)_[A-Za-z0-9]+|"
    r"rk_(?:live|test)_[A-Za-z0-9]+|"
    r"pk_(?:live|test)_[A-Za-z0-9]+|"
    r"whsec_[A-Za-z0-9+/=]+|"
    r"shpat_[A-Za-z0-9]+|"
    r"Bearer\s+[A-Za-z0-9\-._~+/]+=*)",
    re.IGNORECASE,
)


def _mask(value: str) -> str:
    return _SECRET_PATTERN.sub("***REDACTED***", value)


def _sanitize(obj: Any, depth: int = 0) -> Any:
    if depth > 10:
        return obj
    if isinstance(obj, str):
        return _mask(obj)
    if isinstance(obj, dict):
        return {k: _sanitize(v, depth + 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v, depth + 1) for v in obj]
    return obj


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": _mask(record.getMessage()),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        # Copy extra fields the caller passed via extra={...}
        skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "taskName",
        }
        for key, val in record.__dict__.items():
            if key not in skip:
                entry[key] = _sanitize(val)
        return json.dumps(entry, default=str)


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
) -> None:
    """Configure root logger with JSON output. Call once at startup."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers so calling setup_logging() twice is idempotent.
    root.handlers.clear()

    fmt = _JsonFormatter()

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(fmt)
    root.addHandler(stdout_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def mask_secret(value: str) -> str:
    """Public helper: mask any secrets in an arbitrary string."""
    return _mask(value)
