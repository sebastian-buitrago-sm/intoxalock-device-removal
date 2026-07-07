import json
from http import HTTPStatus
from typing import Any

import todo_lambda.handler as handler_module
from todo_lambda.handler import handler

from .routes import Routes


def _post(body: dict[str, Any]) -> dict[str, Any]:
    event = {
        "httpMethod": "POST",
        "path": Routes.TODOS,
        "body": json.dumps(body),
    }
    return handler(event, None)


def test_create_todo_with_only_a_title() -> None:
    response = _post({"title": "Buy milk"})

    assert response["statusCode"] == HTTPStatus.CREATED
    assert response["headers"]["Location"].startswith(f"{Routes.TODOS}/")

    todo = json.loads(response["body"])
    assert todo["title"] == "Buy milk"
    assert todo["description"] is None
    assert todo["completed"] is False
    assert todo["id"]
    assert todo["createdAt"]
    assert todo["updatedAt"]


def test_create_todo_with_title_and_description() -> None:
    response = _post({"title": "Buy milk", "description": "2% and oat milk"})

    assert response["statusCode"] == HTTPStatus.CREATED

    todo = json.loads(response["body"])
    assert todo["title"] == "Buy milk"
    assert todo["description"] == "2% and oat milk"
    assert todo["completed"] is False


def test_title_is_trimmed_before_validation() -> None:
    response = _post({"title": "  Buy milk  "})

    assert response["statusCode"] == HTTPStatus.CREATED
    todo = json.loads(response["body"])
    assert todo["title"] == "Buy milk"


def test_rejecting_a_missing_title() -> None:
    response = _post({})

    assert response["statusCode"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert handler_module._repo.todos == []


def test_rejecting_an_empty_title() -> None:
    response = _post({"title": ""})

    assert response["statusCode"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert handler_module._repo.todos == []


def test_rejecting_a_whitespace_only_title() -> None:
    response = _post({"title": "   "})

    assert response["statusCode"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert handler_module._repo.todos == []


def test_rejecting_a_title_over_the_length_limit() -> None:
    response = _post({"title": "a" * 201})

    assert response["statusCode"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert handler_module._repo.todos == []


def test_rejecting_a_description_over_the_length_limit() -> None:
    response = _post({"title": "Buy milk", "description": "a" * 2001})

    assert response["statusCode"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert handler_module._repo.todos == []


def test_validation_error_is_rfc9457_problem_details() -> None:
    response = _post({"title": ""})

    assert response["statusCode"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response["headers"]["Content-Type"] == "application/problem+json"

    body = json.loads(response["body"])
    assert body["type"] == "about:blank"
    assert body["title"] == HTTPStatus.UNPROCESSABLE_ENTITY.phrase
    assert body["status"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert body["detail"]
    assert body["instance"] == Routes.TODOS
    assert body["errors"][0]["field"] == "title"


def test_unmatched_route_is_problem_details() -> None:
    response = handler({"httpMethod": "GET", "path": Routes.UNKNOWN}, None)

    assert response["statusCode"] == HTTPStatus.NOT_FOUND
    assert response["headers"]["Content-Type"] == "application/problem+json"
    body = json.loads(response["body"])
    assert body["status"] == HTTPStatus.NOT_FOUND
    assert body["title"] == HTTPStatus.NOT_FOUND.phrase


def test_malformed_json_body_is_bad_request() -> None:
    response = handler({"httpMethod": "POST", "path": Routes.TODOS, "body": "{not json"}, None)

    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    assert response["headers"]["Content-Type"] == "application/problem+json"
    body = json.loads(response["body"])
    assert body["title"] == HTTPStatus.BAD_REQUEST.phrase
    assert handler_module._repo.todos == []


def test_non_object_json_body_is_bad_request() -> None:
    response = handler({"httpMethod": "POST", "path": Routes.TODOS, "body": "[]"}, None)

    assert response["statusCode"] == HTTPStatus.BAD_REQUEST
    assert handler_module._repo.todos == []


def test_rejecting_equal_title_and_description() -> None:
    response = _post({"title": "Buy milk", "description": "Buy milk"})

    assert response["statusCode"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert handler_module._repo.todos == []


def test_server_only_fields_are_ignored_on_create() -> None:
    response = _post(
        {
            "title": "Buy milk",
            "id": "client-chosen-id",
            "createdAt": "2000-01-01T00:00:00+00:00",
            "updatedAt": "2000-01-01T00:00:00+00:00",
            "completed": True,
        }
    )

    assert response["statusCode"] == HTTPStatus.CREATED
    todo = json.loads(response["body"])
    assert todo["title"] == "Buy milk"
    assert todo["completed"] is False
    assert todo["id"] != "client-chosen-id"
    assert todo["createdAt"] != "2000-01-01T00:00:00+00:00"
    assert todo["updatedAt"] != "2000-01-01T00:00:00+00:00"
