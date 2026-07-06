# TDD log — slice 01: Create Todo

Feature: `docs/specs/todo-lambda/features/01-create-todo.feature`
All scenarios tagged `@integration` — tests invoke `todo_lambda.handler.handler`
with a synthetic API Gateway proxy event against the in-memory `TodoRepository`
adapter (the "real store" for this app, per project-spec's persistence decision).

## Design

- **Use case**: `CreateTodo` (`features/todos/usecases.py`) — takes a
  `CreateTodoCommand` (frozen), returns a `Todo`, raises `ValidationError`.
- **Port**: `TodoRepository.add(todo: Todo) -> None` (`features/todos/ports.py`).
- **Adapter**: `InMemoryTodoRepository` (`features/todos/adapters.py`) — doubles
  as both the production adapter and the unit-test fake (both are in-memory by
  spec decision, so one class serves both roles).
- **Domain**: `Todo.create(...)` factory (`features/todos/domain.py`) — trims
  title, validates length limits, raises `ValidationError` (shared base in
  `shared/errors.py`, mapped to 422 by `shared/problem.py`).

## Scenarios

- [x] Create a todo with only a title
- [x] Create a todo with title and description
- [x] Title is trimmed before validation
- [x] Rejecting a missing title
- [x] Rejecting an empty title
- [x] Rejecting a whitespace-only title
- [x] Rejecting a title over the length limit
- [x] Rejecting a description over the length limit
- [x] Server-only fields are ignored on create

## Cycles

### Create a todo with only a title
- RED: `tests/integration/test_create_todo.py::test_create_todo_with_only_a_title` — failed with `ModuleNotFoundError: todo_lambda.handler` (module didn't exist).
- GREEN: added `domain.Todo`, `ports.TodoRepository`, `adapters.InMemoryTodoRepository`, `usecases.CreateTodo`/`CreateTodoCommand`, `handlers.create_todo_handler`, composition-root `handler.py`, and shared `errors.DomainError`/`ValidationError` + `problem.problem_response`. Test passes.
- REFACTOR: none needed yet.

### Create a todo with title and description
- RED: `test_create_todo_with_title_and_description` — passed immediately (existing `description` passthrough already covers it). No production change.

### Title is trimmed before validation
- RED: `test_title_is_trimmed_before_validation` — failed: `'  Buy milk  ' == 'Buy milk'`.
- GREEN: `Todo.create` now calls `title.strip()` before storing. Passes.
- REFACTOR: none needed.

### Rejecting a missing title
- Added `tests/integration/conftest.py` (`_fresh_store` autouse fixture) and a
  `todos` property on `InMemoryTodoRepository` — needed to isolate store state
  per test and observe "no todo is persisted" without a read endpoint (not
  built until slice 02).
- RED: `test_rejecting_a_missing_title` — failed with an unhandled
  `pydantic_core.ValidationError` (raw pydantic error escaping instead of a
  422 problem response) because `CreateTodoCommand.title` was typed `str`.
- GREEN: `CreateTodoCommand.title` is now `str | None`; `Todo.create` treats
  `None`/empty-after-trim as invalid and raises the domain `ValidationError`,
  which `handler.py`'s `except DomainError` maps to a 422 problem response.
- REFACTOR: none needed.

### Rejecting an empty title / Rejecting a whitespace-only title
- RED: both tests passed immediately — the `(title or "").strip()` check in
  `Todo.create` already covers empty and whitespace-only strings. No
  production change.

### Rejecting a title over the length limit
- RED: `test_rejecting_a_title_over_the_length_limit` — failed: `201 == 422`.
- GREEN: `Todo.create` now raises `ValidationError` when the trimmed title
  exceeds 200 chars. Passes.
- REFACTOR: none needed.

### Rejecting a description over the length limit
- RED: `test_rejecting_a_description_over_the_length_limit` — failed: `201 == 422`.
- GREEN: `Todo.create` now raises `ValidationError` when `description` exceeds
  2000 chars. Passes.
- REFACTOR: none needed.

### Server-only fields are ignored on create
- RED: `test_server_only_fields_are_ignored_on_create` — passed immediately.
  `create_todo_handler` only ever reads `body["title"]`/`body["description"]`
  into the command, so extra client-supplied `id`/`createdAt`/`updatedAt`/
  `completed` were already inert. No production change.

## Coverage map

| Scenario | Test |
|---|---|
| Create a todo with only a title | `test_create_todo_with_only_a_title` |
| Create a todo with title and description | `test_create_todo_with_title_and_description` |
| Title is trimmed before validation | `test_title_is_trimmed_before_validation` |
| Rejecting a missing title | `test_rejecting_a_missing_title` |
| Rejecting an empty title | `test_rejecting_an_empty_title` |
| Rejecting a whitespace-only title | `test_rejecting_a_whitespace_only_title` |
| Rejecting a title over the length limit | `test_rejecting_a_title_over_the_length_limit` |
| Rejecting a description over the length limit | `test_rejecting_a_description_over_the_length_limit` |
| Server-only fields are ignored on create | `test_server_only_fields_are_ignored_on_create` |

All 9 scenarios green.

## Gates

`make check` — lint, format, mypy (strict), import-linter, pytest — all green.
(One `ruff --fix` needed for import ordering in `conftest.py`.)
