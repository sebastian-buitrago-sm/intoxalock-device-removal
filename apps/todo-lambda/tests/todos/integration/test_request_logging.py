import json
from http import HTTPStatus
from typing import Any, cast

import pytest
from todo_lambda.handler import handler
from todo_lambda.shared.observability import configure_logging

from .routes import Routes


@pytest.fixture(autouse=True)
def _json_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_FORMAT", "json")
    configure_logging(force=True)


class _Context:
    aws_request_id = "req-123"


class _OtherContext:
    aws_request_id = "req-456"


def _request_log_line(captured: str) -> dict[str, Any]:
    events = [json.loads(line) for line in captured.splitlines() if line.strip()]
    matches = [event for event in events if event.get("event") == "request_completed"]
    assert len(matches) == 1
    return cast(dict[str, Any], matches[0])


def test_successful_create_logs_request_fields(capsys: pytest.CaptureFixture[str]) -> None:
    handler(
        {"httpMethod": "POST", "path": Routes.TODOS, "body": json.dumps({"title": "Buy milk"})},
        _Context(),
    )

    line = _request_log_line(capsys.readouterr().out)
    assert line["aws_request_id"] == "req-123"
    assert line["http_method"] == "POST"
    assert line["path"] == Routes.TODOS
    assert line["route"] == "create_todo"
    assert line["status_code"] == HTTPStatus.CREATED


def test_validation_failure_logs_error_field(capsys: pytest.CaptureFixture[str]) -> None:
    handler({"httpMethod": "POST", "path": Routes.TODOS, "body": json.dumps({})}, _Context())

    line = _request_log_line(capsys.readouterr().out)
    assert line["status_code"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert line["error"] == "ValidationError"


def test_no_request_body_is_never_logged(capsys: pytest.CaptureFixture[str]) -> None:
    secret_title = "top-secret-todo-title"
    handler(
        {"httpMethod": "POST", "path": Routes.TODOS, "body": json.dumps({"title": secret_title})},
        _Context(),
    )

    assert secret_title not in capsys.readouterr().out


def test_bound_context_does_not_leak_between_requests(capsys: pytest.CaptureFixture[str]) -> None:
    handler({"httpMethod": "POST", "path": Routes.TODOS, "body": json.dumps({})}, _Context())
    handler({"httpMethod": "GET", "path": Routes.UNKNOWN, "body": None}, _OtherContext())

    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    matches = [event for event in lines if event.get("event") == "request_completed"]
    assert matches[-1]["aws_request_id"] == "req-456"
    assert matches[-1]["http_method"] == "GET"
    assert matches[-1]["path"] == Routes.UNKNOWN
    assert "error" not in matches[-1]
