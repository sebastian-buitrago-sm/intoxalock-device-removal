from todo_lambda.features.todos.domain import Todo


class InMemoryTodoRepository:
    def __init__(self) -> None:
        self._todos: dict[str, Todo] = {}

    def add(self, todo: Todo) -> None:
        self._todos[todo.id] = todo

    @property
    def todos(self) -> list[Todo]:
        return list(self._todos.values())
