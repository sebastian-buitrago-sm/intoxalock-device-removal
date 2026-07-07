import logging
import os
import sys
from typing import cast

import structlog
from structlog.typing import FilteringBoundLogger

_configured = False


def _level_from_env() -> int:
    name = os.environ.get("LOG_LEVEL", "INFO").upper()
    return logging.getLevelNamesMapping().get(name, logging.INFO)


def _render_json() -> bool:
    return os.environ.get("LOG_FORMAT", "json").lower() != "console"


def configure_logging(*, force: bool = False) -> None:
    global _configured
    if _configured and not force:
        return

    renderer = (
        structlog.processors.JSONRenderer() if _render_json() else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(_level_from_env()),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=not force,
    )
    _configured = True


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    return cast(FilteringBoundLogger, structlog.get_logger(name))
