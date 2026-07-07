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


def _canonical_line(captured: str) -> dict[str, Any]:
    events = [json.loads(line) for line in captured.splitlines() if line.strip()]
    canonical = [event for event in events if event.get("event") == "request.completed"]
    assert len(canonical) == 1
    return cast(dict[str, Any], canonical[0])


def test_successful_create_emits_canonical_line(capsys: pytest.CaptureFixture[str]) -> None:
    handler(
        {"httpMethod": "POST", "path": Routes.TODOS, "body": json.dumps({"title": "Buy milk"})},
        _Context(),
    )

    line = _canonical_line(capsys.readouterr().out)
    assert line["aws_request_id"] == "req-123"
    assert line["http_method"] == "POST"
    assert line["path"] == Routes.TODOS
    assert line["route"] == "create_todo"
    assert line["status_code"] == HTTPStatus.CREATED
    assert line["outcome"] == "success"


def test_validation_failure_emits_client_error_line(capsys: pytest.CaptureFixture[str]) -> None:
    handler({"httpMethod": "POST", "path": Routes.TODOS, "body": json.dumps({})}, _Context())

    line = _canonical_line(capsys.readouterr().out)
    assert line["status_code"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert line["outcome"] == "client_error"
    assert line["error"] == "ValidationError"


def test_no_request_body_is_never_logged(capsys: pytest.CaptureFixture[str]) -> None:
    secret_title = "top-secret-todo-title"
    handler(
        {"httpMethod": "POST", "path": Routes.TODOS, "body": json.dumps({"title": secret_title})},
        _Context(),
    )

    assert secret_title not in capsys.readouterr().out
