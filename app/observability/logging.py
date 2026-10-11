
"""Centralized logging configuration with request correlation."""

import logging
import sys
from contextvars import ContextVar, Token


request_id_context: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)


def set_request_id(request_id: str) -> Token[str]:
    """Set the request ID for the current execution context."""
    return request_id_context.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    """Restore the previous request ID context."""
    request_id_context.reset(token)


class RequestContextFilter(logging.Filter):
    """Add a request ID to log records when one is not already present."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_context.get()
        return True


LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "request_id=%(request_id)s | %(message)s"
)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure application-wide logging."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(RequestContextFilter())

    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger using the centralized application configuration."""
    return logging.getLogger(name)