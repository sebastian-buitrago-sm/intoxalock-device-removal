import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http import HTTPStatus

from structlog.contextvars import bind_contextvars, clear_contextvars
from structlog.typing import FilteringBoundLogger

CANONICAL_EVENT = "request.completed"

_LEVEL_BY_OUTCOME = {
    "server_error": logging.ERROR,
    "client_error": logging.WARNING,
}


@dataclass
class CanonicalEntry:
    fields: dict[str, object] = field(default_factory=dict)

    def record(self, **fields: object) -> None:
        self.fields.update({key: value for key, value in fields.items() if value is not None})


def _outcome_for(status: object) -> str:
    if not isinstance(status, int):
        return "unknown"
    if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
        return "server_error"
    if status >= HTTPStatus.BAD_REQUEST:
        return "client_error"
    return "success"


def _present(fields: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in fields.items() if value is not None}


@contextmanager
def canonical_log(logger: FilteringBoundLogger, **context: object) -> Iterator[CanonicalEntry]:
    """Emit exactly one wide log line summarizing the whole invocation.

    Context bound here rides along on the single canonical line via
    ``contextvars``, so use cases and adapters can enrich it without taking
    the logger as a dependency.
    """
    clear_contextvars()
    bind_contextvars(**_present(context))
    entry = CanonicalEntry()
    start = time.monotonic()
    try:
        yield entry
    except BaseException:
        entry.record(outcome="server_error")
        logger.exception(CANONICAL_EVENT, duration_ms=_elapsed_ms(start), **entry.fields)
        raise
    else:
        outcome = _outcome_for(entry.fields.get("status_code"))
        entry.record(outcome=outcome)
        level = _LEVEL_BY_OUTCOME.get(outcome, logging.INFO)
        logger.log(level, CANONICAL_EVENT, duration_ms=_elapsed_ms(start), **entry.fields)
    finally:
        clear_contextvars()


def _elapsed_ms(start: float) -> float:
    return round((time.monotonic() - start) * 1000, 3)
