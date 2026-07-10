from typing import Protocol

from todo_lambda.features.todos.domain import Todo


class TodoRepository(Protocol):
    def add(self, todo: Todo) -> None: ...
