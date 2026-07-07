import json
from http import HTTPStatus
from typing import Any, cast

import pytest
from todo_lambda.shared.observability import canonical_log, configure_logging, get_logger


@pytest.fixture(autouse=True)
def _json_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_FORMAT", "json")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    configure_logging(force=True)


def _last_line(captured: str) -> dict[str, Any]:
    lines = [line for line in captured.splitlines() if line.strip()]
    return cast(dict[str, Any], json.loads(lines[-1]))


def test_emits_one_wide_line_with_bound_context(capsys: pytest.CaptureFixture[str]) -> None:
    log = get_logger("test")
    with canonical_log(log, aws_request_id="req-1", http_method="POST", path="/todos") as entry:
        entry.record(status_code=HTTPStatus.CREATED, route="create_todo")

    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(lines) == 1

    line = json.loads(lines[0])
    assert line["event"] == "request.completed"
    assert line["aws_request_id"] == "req-1"
    assert line["http_method"] == "POST"
    assert line["path"] == "/todos"
    assert line["route"] == "create_todo"
    assert line["status_code"] == HTTPStatus.CREATED
    assert line["outcome"] == "success"
    assert line["level"] == "info"
    assert isinstance(line["duration_ms"], (int, float))


@pytest.mark.parametrize(
    ("status", "outcome", "level"),
    [
        (HTTPStatus.OK, "success", "info"),
        (HTTPStatus.BAD_REQUEST, "client_error", "warning"),
        (HTTPStatus.UNPROCESSABLE_ENTITY, "client_error", "warning"),
        (HTTPStatus.INTERNAL_SERVER_ERROR, "server_error", "error"),
    ],
)
def test_outcome_and_level_derive_from_status(
    capsys: pytest.CaptureFixture[str],
    status: HTTPStatus,
    outcome: str,
    level: str,
) -> None:
    log = get_logger("test")
    with canonical_log(log) as entry:
        entry.record(status_code=status)

    line = _last_line(capsys.readouterr().out)
    assert line["outcome"] == outcome
    assert line["level"] == level


def test_none_values_are_dropped(capsys: pytest.CaptureFixture[str]) -> None:
    log = get_logger("test")
    with canonical_log(log, aws_request_id=None, http_method="GET") as entry:
        entry.record(status_code=HTTPStatus.OK, route=None)

    line = _last_line(capsys.readouterr().out)
    assert "aws_request_id" not in line
    assert "route" not in line


def test_exception_emits_server_error_line_then_reraises(
    capsys: pytest.CaptureFixture[str],
) -> None:
    log = get_logger("test")
    with pytest.raises(ValueError):
        with canonical_log(log, aws_request_id="req-2") as entry:
            entry.record(route="create_todo")
            raise ValueError("boom")

    line = _last_line(capsys.readouterr().out)
    assert line["event"] == "request.completed"
    assert line["outcome"] == "server_error"
    assert line["level"] == "error"
    assert line["aws_request_id"] == "req-2"
    assert "boom" in line["exception"]


def test_context_does_not_leak_between_requests(capsys: pytest.CaptureFixture[str]) -> None:
    log = get_logger("test")
    with canonical_log(log, aws_request_id="req-a") as entry:
        entry.record(status_code=HTTPStatus.OK)
    with canonical_log(log, http_method="GET") as entry:
        entry.record(status_code=HTTPStatus.OK)

    second = _last_line(capsys.readouterr().out)
    assert "aws_request_id" not in second
