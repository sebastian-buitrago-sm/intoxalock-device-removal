# Judge verdict — slice 01: Create Todo (review pass 3)

Full independent re-review from scratch. Nothing from `judge_01-create-todo.md`
(review 1 or 2) or the TDD log was taken on trust; baseline docs, feature file,
plan, spec, all current source under
`apps/todo-lambda/src/todo_lambda/`, all current tests under
`apps/todo-lambda/tests/`, and all four gates were re-read/re-run directly.

## Scope of this pass

Since review 2: the fabricated `_title_and_description_differ` rule and its
test were deleted (commit `01a7714`), and `tdd_01-create-todo.md` was rewritten
with a "Post-judge reconciliation" section documenting the `Todo.create` →
pydantic `Field`/`field_validator` rewrite, the composition-root error-boundary
additions (`BadRequest`/400, unmatched-route/404, RFC 9457 `errors` extension),
and the fabricated rule's removal. This review verifies all of that from the
current disk state and hunts independently for anything still off.

## 1. Scenario → test coverage matrix

`docs/specs/todo-lambda/features/01-create-todo.feature` tags the whole
feature `@slice-01 @integration` (no per-scenario override) — every scenario
should be, and is, covered by an integration test invoking
`todo_lambda.handler.handler` in `apps/todo-lambda/tests/todos/integration/test_create_todo.py`.

| # | `@scenario` | Test | Status |
|---|---|---|---|
| 1 | Create a todo with only a title | `test_create_todo_with_only_a_title` (`test_create_todo.py:20-32`) | Covered |
| 2 | Create a todo with title and description | `test_create_todo_with_title_and_description` (`:35-43`) | Covered |
| 3 | Title is trimmed before validation | `test_title_is_trimmed_before_validation` (`:46-51`) | Covered |
| 4 | Rejecting a missing title | `test_rejecting_a_missing_title` (`:54-58`) | Covered |
| 5 | Rejecting an empty title | `test_rejecting_an_empty_title` (`:61-65`) | Covered |
| 6 | Rejecting a whitespace-only title | `test_rejecting_a_whitespace_only_title` (`:68-72`) | Covered |
| 7 | Rejecting a title over the length limit | `test_rejecting_a_title_over_the_length_limit` (`:75-79`) | Covered |
| 8 | Rejecting a description over the length limit | `test_rejecting_a_description_over_the_length_limit` (`:82-86`) | Covered |
| 9 | Server-only fields are ignored on create | `test_server_only_fields_are_ignored_on_create` (`:131-148`) | Covered |

9/9 scenarios mapped 1:1 to a passing test. No gap.

Extra tests not tied to any `@scenario` — `test_validation_error_is_rfc9457_problem_details`,
`test_unmatched_route_is_problem_details`, `test_malformed_json_body_is_bad_request`,
`test_non_object_json_body_is_bad_request` (`test_create_todo.py:89-128`) — cover
composition-root error-boundary behavior that `docs/architecture/conventions.md:19`
mandates app-wide (400/404/422/500 all map at the single boundary), not something
specific to slice 01's scenarios. This is legitimate infrastructure, correctly
attributed and explained in the TDD log's reconciliation section (see §2), not a
repeat of the fabricated-rule problem — but it is still cross-cutting behavior
riding inside a single-feature slice's test file with no scenario of its own, as
review 2 already flagged. Non-blocking; carried forward as a process note (see §4).

## 2. TDD discipline

Re-read `docs/specs/todo-lambda/progress/tdd_01-create-todo.md` end to end
against the current source and `git log`/`git diff`:

- The original 9 RED→GREEN cycles (lines 45-92) match what a plain
  `Todo.create`-factory implementation would have looked like — plausible,
  internally consistent narrative.
- The "Post-judge reconciliation" section (lines 115-194) now explicitly
  documents, with file:line citations, the `Todo.create` → `pydantic.Field` +
  `field_validator` rewrite and the resulting error-body-shape change,
  attributes the `BadRequest`/unmatched-route/RFC 9457-extension additions to
  commit `2b05e30`, and documents the fabricated `_title_and_description_differ`
  rule and its removal in commit `01a7714`, including *why* it was fabricated
  (no basis in the `.feature`, `project-spec.md`, or `plan.md`) and how it was
  confirmed gone (grep, re-running `make check`).
- I independently verified the fabricated rule is gone:
  `grep -rn "title_and_description_differ\|equal_title_and_description\|model_validator" apps/todo-lambda/src apps/todo-lambda/tests`
  returns nothing. `git diff` of `features/todos/domain/todo.py` and
  `tests/todos/integration/test_create_todo.py` (uncommitted-but-consistent
  with the log) shows only the rule and its test removed, no residue.
- This reconciliation is retrospective narration rather than a live cycle log,
  but it accurately and specifically matches what's on disk — no more silent
  gaps between "what the log says happened" and "what the code does" for the
  items review 2 called out.
- One item from review 2's required changes remains formally outstanding:
  "stop editing `docs/architecture/*` from inside a slice's build/reconciliation
  commit." `docs/architecture/conventions.md` and `docs/architecture/slice-structure.md`
  were edited inside commit `2b05e30` (the todo-lambda restructuring commit) and
  have not since been split into their own reviewed change; the TDD log's
  reconciliation section doesn't mention this item at all (only items 1 and 3
  from review 2 are addressed, not item 2's process complaint). The doc content
  itself is accurate to the shipped behavior (verified: `conventions.md:13,19-23`
  and `slice-structure.md:19,21,29` match `handler.py`'s actual error-boundary
  and package-per-layer structure). Given three review cycles have passed, the
  doc content is correct, and undoing it now would mean rewriting already-reviewed
  git history rather than fixing a code defect, I'm treating this as a
  **non-blocking, still-open process note** rather than grounds to block this
  pass — see §4.
- New finding from this pass, not raised in review 1 or 2: the domain
  `ValidationError`/`DomainError` taxonomy (`shared/domain/errors.py:1-6`) and
  the `_STATUS_BY_ERROR` map + `except (DomainError, ...)` branch built for it
  (`shared/handlers/problem.py:9-18`, `handler.py:59`) are dead code for this
  slice: `grep -rn "raise ValidationError\|raise DomainError" apps/todo-lambda/src`
  returns nothing. Since the `Todo.create` factory was replaced by direct
  `pydantic.Field`/`field_validator` construction, every validation failure in
  this slice now raises `pydantic.ValidationError` directly — the domain error
  taxonomy and its status map are never exercised by any test. This isn't a
  fabricated rule (it matches the anticipated taxonomy `conventions.md:21`
  explicitly calls for — "`NotFoundError`→404, `ConflictError`→409, etc. as
  slices need them"), but it is currently untested production scaffolding, a
  mild TDD-discipline gap. Non-blocking for slice 01 (no scenario needs it
  yet), but worth a note so it isn't forgotten once slice 02+ actually raises
  a `DomainError` subclass.

## 3. Architecture

- **Domain purity**: `features/todos/domain/todo.py:1-17` imports only
  `datetime` and `pydantic` — no I/O, `boto3`, or AWS types. Validation
  (`Field(min_length=1, max_length=200)`, `max_length=2000`, trim
  `field_validator`) enforces only the spec's business invariants (Rules 1-2).
- **Usecases depend on ports, not adapters**: `usecases/create_todo.py:6-7`
  imports `domain.Todo` and `ports.TodoRepository` only; `CreateTodo.__init__`
  takes a `TodoRepository` (`:16-17`), never an adapter type.
- **Composition root is the only wiring point**: `handler.py:21` builds the
  singleton `InMemoryTodoRepository`; `handler.py:42` builds `CreateTodo(_repo)`
  per request and hands the fully-built use case to
  `create_todo_handler` (`handlers/create_todo.py:22`) — the handler never
  constructs an adapter, matching `slice-structure.md:30`.
- **Handlers stay happy-path**: `handlers/create_todo.py:22-31` parses the
  body, builds the command, calls the use case, renders `201` — no
  try/except, no business logic. Errors propagate to `handler.py`'s
  `_dispatch` (lines 39-76), the single error boundary, matching
  `conventions.md:19`.
- **RFC 9457 compliance**: `shared/handlers/problem.py:28-53` emits the five
  standard members (`type: about:blank`, `title` = status phrase, `status`,
  `detail`, `instance`) plus optional `traceId`/`errors` extensions, matching
  `conventions.md:23`. Verified live via
  `test_validation_error_is_rfc9457_problem_details` (`test_create_todo.py:89-101`).
- **Structured logging**: `shared/observability/config.py` configures
  `structlog` once at cold start (module-level `_configured` guard);
  `handler.py:28` wraps every invocation in `canonical_log`, emitting one wide
  `request.completed` line per request (`shared/observability/canonical.py:41-66`).
  `test_no_request_body_is_never_logged` (`test_canonical_logging.py:53-60`)
  confirms the title/body text never appears in the log output. No `print()`
  or secret-like literals found anywhere under `apps/todo-lambda/src`
  (checked via grep).
- **Reuse ladder**: `shared/domain`, `shared/handlers`, `shared/observability`
  are app-local shared code, but they back the app's single composition root
  (not a second slice) — this is app-wide infra the composition root always
  needs, not a slice's business logic promoted prematurely. Not a ladder
  violation.
- **REST conventions**: status codes/methods/paths are constants throughout
  production code (`HTTPStatus.CREATED`, `HTTPMethod.POST`, `TODOS` from
  `handlers/routes.py:1`) — no literal strings/ints used for these in `src/`.

Carried-over, still non-blocking, unchanged since review 2:
- `TodoRepository.add` (`ports/todo_repository.py:6-7`) is still a generic
  CRUD-style port name rather than a use-case-driven one
  (`slice-structure.md:17`). Minor for a one-method port.
- `InMemoryTodoRepository.todos` (`adapters/in_memory_todo_repository.py:11-13`)
  remains a test-only public property on the production adapter, used by
  `test_create_todo.py` (e.g. lines 58, 65, 72, 79, 86, 121, 128) via
  `handler_module._repo.todos` to assert "no todo is persisted" — reaching
  into the composition root's private `_repo` singleton and the adapter's
  internals rather than asserting purely through the handler's public
  response. Pre-agreed as unavoidable until slice 02 adds a `GET`; not worse
  than before.

## 4. Test quality

- Tests assert on the handler's response (status code, headers, body) for
  every scenario — no reach into use case or domain internals for the
  happy-path/validation assertions.
- The "no todo is persisted" assertions do reach adapter internals
  (`handler_module._repo.todos`, per above) — acceptable pre-agreed
  workaround, not new.
- Minor test-quality nit: `test_create_todo_with_only_a_title`
  (`test_create_todo.py:20-32`) only asserts
  `response["headers"]["Location"].startswith(f"{Routes.TODOS}/")` — it
  never checks the Location value actually equals `f"{Routes.TODOS}/{todo['id']}"`.
  A handler bug that put a *different* id in the Location header would still
  pass this test, even though the scenario says "pointing to the created
  todo." Non-blocking (same weakness existed in prior passes; not new or
  worse), but worth tightening.
- Trophy tags: the `.feature` file's single `@integration` tag at the feature
  level is honored — every driving test lives under
  `tests/todos/integration/` and invokes the real `handler`, no
  unit-level mocked-DB middle tier introduced.

## 5. Gates (re-run independently, not trusted from any log)

All four green, run fresh in this session:

- `make lint` → `ruff check .` all checks passed; `ruff format --check .` 44 files already formatted.
- `make typecheck` → `mypy` — Success: no issues found in 44 source files.
- `make imports` → `lint-imports` — Analyzed 44 files, 62 dependencies, 1 contract kept, 0 broken.
- `make test` → `pytest` — 26 passed (includes `apps/elevenlabs-agent`'s 2 unrelated tests, `apps/todo-lambda`'s 24: 8 observability-unit, 3 canonical-logging-integration, 13 create-todo-integration).

## Summary

All three of review 2's blocking findings have real substance behind their
fixes: the fabricated `title != description` rule is gone (confirmed by grep
and diff, not just log narration), and the domain rewrite plus the
composition-root error-boundary additions are now documented in
`tdd_01-create-todo.md` with specific file:line citations that match what's
actually on disk. Scenario coverage remains 9/9. All four gates are green,
independently re-run. No new fabricated/unspecified business rule was found in
this independent pass. The two items still open — docs/architecture edited
inside the slice's own commit (review 2, item 3, still not split out), and a
newly-noticed untested `DomainError` taxonomy branch — are process/scaffolding
notes rather than defects in current, observable behavior, and don't meet the
bar (failing gate / unmapped scenario / untested business logic) for blocking.

## Required changes

None.

APPROVED -> docs/specs/todo-lambda/progress/judge_01-create-todo.md
