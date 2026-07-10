import json
from http import HTTPStatus
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from todo_lambda.shared.domain import DomainError, ValidationError

_STATUS_BY_ERROR: dict[type[DomainError], HTTPStatus] = {
    ValidationError: HTTPStatus.UNPROCESSABLE_ENTITY,
}


def _status_for(error: DomainError) -> HTTPStatus:
    for klass in type(error).__mro__:
        if klass in _STATUS_BY_ERROR:
            return _STATUS_BY_ERROR[klass]
    return HTTPStatus.INTERNAL_SERVER_ERROR


def _field_errors(error: PydanticValidationError) -> list[dict[str, str]]:
    return [
        {"field": ".".join(str(part) for part in item["loc"]), "detail": item["msg"]}
        for item in error.errors()
    ]


def problem(
    status: HTTPStatus,
    detail: str,
    *,
    instance: str | None = None,
    trace_id: str | None = None,
    extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
    }
    if instance is not None:
        body["instance"] = instance
    if trace_id is not None:
        body["traceId"] = trace_id
    if extensions:
        body.update(extensions)

    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/problem+json"},
        "body": json.dumps(body),
    }


def problem_response(
    error: DomainError | PydanticValidationError,
    *,
    instance: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if isinstance(error, PydanticValidationError):
        return problem(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "The request parameters failed validation.",
            instance=instance,
            trace_id=trace_id,
            extensions={"errors": _field_errors(error)},
        )
    return problem(_status_for(error), str(error), instance=instance, trace_id=trace_id)
