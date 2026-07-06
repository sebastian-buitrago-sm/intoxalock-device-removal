from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel

from todo_lambda.features.todos.domain import Todo
from todo_lambda.features.todos.ports import TodoRepository


class CreateTodoCommand(BaseModel, frozen=True):
    title: str | None = None
    description: str | None = None


class CreateTodo:
    def __init__(self, repo: TodoRepository) -> None:
        self._repo = repo

    def __call__(self, command: CreateTodoCommand) -> Todo:
        todo = Todo.create(
            id=str(uuid4()),
            title=command.title,
            description=command.description,
            created_at=datetime.now(UTC),
        )
        self._repo.add(todo)
        return todo
