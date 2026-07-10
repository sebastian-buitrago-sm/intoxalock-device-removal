from http import HTTPMethod, HTTPStatus
from typing import Any

from pydantic import ValidationError as PydanticValidationError
from structlog.contextvars import bind_contextvars, clear_contextvars

from todo_lambda.features.todos.adapters import InMemoryTodoRepository
from todo_lambda.features.todos.handlers import TODOS, create_todo_handler
from todo_lambda.features.todos.usecases import CreateTodo
from todo_lambda.shared.domain import DomainError
from todo_lambda.shared.handlers import BadRequest, problem, problem_response
from todo_lambda.shared.observability import configure_logging, get_logger

configure_logging()

_log = get_logger("todo_lambda.request")
_repo = InMemoryTodoRepository()


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    method = event.get("httpMethod")
    path = event.get("path")
    trace_id = getattr(context, "aws_request_id", None)
    bind_contextvars(aws_request_id=trace_id, http_method=method, path=path)
    try:
        return _dispatch(event, method, path, trace_id)
    finally:
        clear_contextvars()


def _dispatch(
    event: dict[str, Any],
    method: str | None,
    path: str | None,
    trace_id: str | None,
) -> dict[str, Any]:
    try:
        if method == HTTPMethod.POST and path == TODOS:
            return _log_and_return(
                create_todo_handler(event, CreateTodo(_repo)), route="create_todo"
            )
        return _log_and_return(
            problem(
                HTTPStatus.NOT_FOUND,
                f"No route matches {method} {path}.",
                instance=path,
                trace_id=trace_id,
            ),
            route="unmatched",
        )
    except BadRequest as error:
        return _log_and_return(
            problem(HTTPStatus.BAD_REQUEST, str(error), instance=path, trace_id=trace_id),
            error=type(error).__name__,
        )
    except (DomainError, PydanticValidationError) as error:
        return _log_and_return(
            problem_response(error, instance=path, trace_id=trace_id),
            error=type(error).__name__,
        )
    except Exception as error:
        response = problem(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "An unexpected error occurred.",
            instance=path,
            trace_id=trace_id,
        )
        _log.exception(
            "request_completed", error=type(error).__name__, status_code=response["statusCode"]
        )
        return response


def _log_and_return(response: dict[str, Any], **fields: object) -> dict[str, Any]:
    _log.info("request_completed", status_code=response["statusCode"], **fields)
    return response
