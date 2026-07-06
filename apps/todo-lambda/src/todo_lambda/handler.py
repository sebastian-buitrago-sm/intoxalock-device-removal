from typing import Any

from todo_lambda.features.todos.adapters import InMemoryTodoRepository
from todo_lambda.features.todos.handlers import create_todo_handler
from todo_lambda.features.todos.usecases import CreateTodo
from todo_lambda.shared.errors import DomainError
from todo_lambda.shared.problem import problem_response

_repo = InMemoryTodoRepository()


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    method = event.get("httpMethod")
    path = event.get("path")
    try:
        if method == "POST" and path == "/todos":
            return create_todo_handler(event, CreateTodo(_repo))
    except DomainError as error:
        return problem_response(error)

    return {"statusCode": 404, "body": ""}
