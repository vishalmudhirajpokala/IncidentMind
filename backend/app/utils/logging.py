"""Structured JSON logging with request correlation IDs.

Design rules enforced here:
  * every log record is a single JSON object (machine readable)
  * a correlation id (`request_id`) is attached to every record emitted while
    handling a request
  * secret-looking values are redacted before they are ever written
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

# --------------------------------------------------------------------------
# request correlation
# --------------------------------------------------------------------------
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_incident_id: ContextVar[Optional[str]] = ContextVar("incident_id", default=None)

# Keys whose values must never be written to logs.
_SECRET_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "groq_api_key",
    "hindsight_api_key",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "private_key",
}
_REDACTED = "***redacted***"
_MAX_VALUE_LEN = 2000


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


def set_request_id(value: Optional[str]) -> None:
    _request_id.set(value)


def get_request_id() -> Optional[str]:
    return _request_id.get()


def set_incident_id(value: Optional[str]) -> None:
    _incident_id.set(value)


def get_incident_id() -> Optional[str]:
    return _incident_id.get()


# --------------------------------------------------------------------------
# redaction
# --------------------------------------------------------------------------
def redact(value: Any, _depth: int = 0) -> Any:
    """Recursively redact secret-looking keys and truncate long values."""
    if _depth > 6:
        return "<max-depth>"
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, val in value.items():
            if isinstance(key, str) and key.lower() in _SECRET_KEYS:
                out[key] = _REDACTED
            else:
                out[key] = redact(val, _depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [redact(v, _depth + 1) for v in value]
    if isinstance(value, str) and len(value) > _MAX_VALUE_LEN:
        return value[:_MAX_VALUE_LEN] + f"...<truncated {len(value) - _MAX_VALUE_LEN} chars>"
    return value


# --------------------------------------------------------------------------
# formatter
# --------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", None) or _request_id.get()
        if request_id:
            payload["request_id"] = request_id
        incident_id = getattr(record, "incident_id", None) or _incident_id.get()
        if incident_id:
            payload["incident_id"] = incident_id

        # any extra kwargs passed via logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key.startswith("event_"):
                payload[key[len("event_") :]] = redact(value)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(redact(payload), default=str)


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Install the structured handler on the root logger (idempotent)."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s")
        )
    root.addHandler(handler)

    # uvicorn access logs would be unstructured; route them through ours.
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.access").propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
