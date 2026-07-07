import json
from http import HTTPStatus
from typing import Any

from todo_lambda.features.todos.domain import Todo
from todo_lambda.features.todos.handlers.routes import TODOS
from todo_lambda.features.todos.usecases import CreateTodo, CreateTodoCommand
from todo_lambda.shared.handlers import parse_json_object


def _todo_to_dict(todo: Todo) -> dict[str, Any]:
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
        "createdAt": todo.created_at.isoformat(),
        "updatedAt": todo.updated_at.isoformat(),
    }


def create_todo_handler(event: dict[str, Any], usecase: CreateTodo) -> dict[str, Any]:
    body = parse_json_object(event.get("body"))
    command = CreateTodoCommand(title=body.get("title"), description=body.get("description"))
    todo = usecase(command)

    return {
        "statusCode": HTTPStatus.CREATED,
        "headers": {"Location": f"{TODOS}/{todo.id}"},
        "body": json.dumps(_todo_to_dict(todo)),
    }
