import pytest
import todo_lambda.handler as handler_module
from todo_lambda.features.todos.adapters import InMemoryTodoRepository


@pytest.fixture(autouse=True)
def _fresh_store() -> None:
    handler_module._repo = InMemoryTodoRepository()
