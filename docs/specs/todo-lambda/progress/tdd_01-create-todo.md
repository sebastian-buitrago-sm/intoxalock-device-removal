# TDD log — slice 01: Create Todo

Feature: `docs/specs/todo-lambda/features/01-create-todo.feature`
All scenarios tagged `@integration` — tests invoke `todo_lambda.handler.handler`
with a synthetic API Gateway proxy event against the in-memory `TodoRepository`
adapter (the "real store" for this app, per project-spec's persistence decision).

## Design

As originally built (see "Post-judge reconciliation" below for what changed
after review):

- **Use case**: `CreateTodo` (`features/todos/usecases.py`) — takes a
  `CreateTodoCommand` (frozen), returns a `Todo`, raises `ValidationError`.
- **Port**: `TodoRepository.add(todo: Todo) -> None` (`features/todos/ports.py`).
- **Adapter**: `InMemoryTodoRepository` (`features/todos/adapters.py`) — doubles
  as both the production adapter and the unit-test fake (both are in-memory by
  spec decision, so one class serves both roles).
- **Domain**: `Todo.create(...)` factory (`features/todos/domain.py`) — trims
  title, validates length limits, raises `ValidationError` (shared base in
  `shared/errors.py`, mapped to 422 by `shared/problem.py`).

As it stands now, after the restructuring + reconciliation: the same
use case/port/adapter split, but each layer lives in its own package
(`features/todos/{domain,ports,usecases,adapters,handlers}/`), `Todo`
validates itself via `pydantic.Field` constraints + a `field_validator`
trim (no more `Todo.create` factory), and validation failures are caught
centrally in `handler.py` and rendered as RFC 9457 responses by
`shared/handlers/problem.py`.

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

## Post-judge reconciliation

`judge_01-create-todo.md` returned CHANGES_REQUESTED (3 blocking findings):
`make imports` failing (stale `lambda_hello` reference in the import-linter
config after `apps/lambda-hello` was removed), an undocumented rewrite of
`domain.py`, and missing cold-start structured logging.

Commit `2b05e30` ("refactor(todo-lambda): restructure into nested slice
modules and add observability") addressed all three: dropped `lambda_hello`
from `pyproject.toml`'s import-linter config alongside removing
`apps/lambda-hello`, added `shared/observability/` (`structlog`-based
cold-start logger + canonical per-invocation log line in `handler.py`), and
split the flat feature modules (`domain.py`, `ports.py`, `adapters.py`,
`usecases.py`, `handlers.py`) into per-concern package directories
(`domain/todo.py`, `ports/todo_repository.py`,
`adapters/in_memory_todo_repository.py`, `usecases/create_todo.py`,
`handlers/create_todo.py` + `handlers/routes.py`), with `shared/errors.py` and
`shared/problem.py` moved under `shared/domain/` and `shared/handlers/`
respectively. Tests were reorganized under `tests/todos/` and gained explicit
canonical-logging coverage (`tests/todos/integration/test_canonical_logging.py`,
`tests/shared/observability/test_canonical.py`).

Re-ran `make check` post-refactor: lint, format, mypy (strict), import-linter,
and pytest (27 passed) all green. All 9 slice-01 scenarios still pass under
their new test paths.

**This reconciliation note was itself incomplete** — a second judge pass
(`judge_01-create-todo.md`, re-review) found it omitted two things:

1. `features/todos/domain/todo.py`'s `Todo.create(...)` classmethod factory
   (the version this log documents above) was replaced by direct
   `Todo(...)` construction from `CreateTodo.__call__`
   (`usecases/create_todo.py:19-28`), with validation moved onto the model
   itself: `title`/`description` are now `pydantic.Field(min_length=...,
   max_length=...)`, and a `mode="before"` `field_validator` on `title`
   does the trim. A raw `pydantic.ValidationError` from these constraints
   now propagates out of `Todo(...)` and is caught centrally in
   `handler.py`'s dispatch (`except (DomainError, PydanticValidationError)`),
   translated to a 422 RFC 9457 body with a structured `errors` extension
   (`shared/handlers/problem.py:56-70`) instead of the domain raising its
   own `ValidationError(message)` string. Net effect on this slice's 9
   scenarios: identical (`statusCode` 422, no todo persisted); the response
   body's error shape changed from `{"status":422,"title":"<message>"}` to
   the RFC 9457 `type`/`title`/`status`/`detail`/`errors[]` shape — no
   scenario asserts on that shape, so nothing broke, but this is a real,
   previously-unlogged design change to the domain layer.
2. The same commit added `BadRequest`→400 for malformed/non-object JSON
   bodies (`shared/handlers/request.py`, tests
   `test_malformed_json_body_is_bad_request` /
   `test_non_object_json_body_is_bad_request`), a 404 problem response for
   unmatched routes (`test_unmatched_route_is_problem_details`), and an
   explicit RFC 9457 `errors` extension for field-level pydantic failures
   (`test_validation_error_is_rfc9457_problem_details`) — all composition-
   root/error-boundary infrastructure, not tied to any single `@scenario`
   in `01-create-todo.feature`, and not previously logged as cycles.
3. It also included a **fabricated, unspecified rule**:
   `_title_and_description_differ` rejected any create request where
   `title == description`, with a passing test
   (`test_rejecting_equal_title_and_description`). This has no basis in
   `01-create-todo.feature`, `project-spec.md`'s "Rules & edge cases," or
   `plan.md` — a legitimate request like `{"title": "Fix bug",
   "description": "Fix bug"}` would have been wrongly rejected with 422.

### Removing the fabricated rule
- Deleted `_title_and_description_differ` (`domain/todo.py`) and
  `test_rejecting_equal_title_and_description` (`test_create_todo.py`) —
  no spec basis, confirmed by grepping the `.feature`/spec/plan for any
  title/description-equality rule and finding none. Removed the now-unused
  `ValidationError`/`model_validator` imports from `domain/todo.py`.
- Re-ran `make check`: lint, format, mypy (strict), import-linter, pytest
  (26 passed) all green. All 9 slice-01 scenarios still pass.

The `field_validator`/`Field`-constraint rewrite and the composition-root
error-boundary additions (items 1 and 2 above) are kept as-is — both are
architecturally sound and covered by passing tests — but are recorded here,
for the first time, as the actual production changes they were. Going
forward, cross-cutting composition-root behavior like malformed-body
handling and unmatched-route responses should get its own scenario coverage
(or an explicit note in `plan.md`) rather than arriving inside another
slice's build/reconciliation commit.
