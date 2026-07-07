# Judge verdict — slice 01: Create Todo

## Baseline read

- `docs/architecture.md`, `docs/architecture/slice-structure.md`, `docs/architecture/conventions.md`
- `docs/specs/todo-lambda/features/01-create-todo.feature`
- `docs/specs/todo-lambda/plan.md`
- `docs/specs/todo-lambda/progress/tdd_01-create-todo.md`
- `docs/specs/todo-lambda/project-spec.md`
- Source: `apps/todo-lambda/src/todo_lambda/**`, tests: `apps/todo-lambda/tests/**`

Noted per the task's framing and not re-litigated: the in-memory persistence
decision (`project-spec.md` "Decisions" table, row "Persistence"), and
`InMemoryTodoRepository` doubling as both production adapter and test fake
(`tdd_01-create-todo.md` "Design" section) are pre-agreed simplifications.
Evaluated below rather than flagged on sight.

## Scenario → test coverage matrix

| # | Scenario (`01-create-todo.feature`) | Test | Verdict |
|---|---|---|---|
| 1 | Create a todo with only a title | `test_create_todo_with_only_a_title` (`test_create_todo.py:17`) | covered |
| 2 | Create a todo with title and description | `test_create_todo_with_title_and_description` (`:32`) | covered |
| 3 | Title is trimmed before validation | `test_title_is_trimmed_before_validation` (`:43`) | covered |
| 4 | Rejecting a missing title | `test_rejecting_a_missing_title` (`:51`) | covered |
| 5 | Rejecting an empty title | `test_rejecting_an_empty_title` (`:58`) | covered |
| 6 | Rejecting a whitespace-only title | `test_rejecting_a_whitespace_only_title` (`:65`) | covered |
| 7 | Rejecting a title over the length limit | `test_rejecting_a_title_over_the_length_limit` (`:72`) | covered |
| 8 | Rejecting a description over the length limit | `test_rejecting_a_description_over_the_length_limit` (`:79`) | covered |
| 9 | Server-only fields are ignored on create | `test_server_only_fields_are_ignored_on_create` (`:86`) | covered |

All 9 `@scenario`s have a concrete, 1:1 integration test. No coverage gap.

## Gates — re-run myself, current repo state

- `make lint` — **PASS** (ruff check + format, all files formatted).
- `make typecheck` — **PASS** (`mypy`: "Success: no issues found in 26 source files").
- `make imports` — **FAIL**:
  ```
  uv run lint-imports
  Could not find package 'lambda_hello' in your Python path.
  make: *** [imports] Error 1
  ```
- `make test` — **PASS** (11 passed: 9 create-todo integration tests + 2 pre-existing `elevenlabs-agent` CLI tests).

`make imports` fails reproducibly (confirmed on repeated runs). Root cause:
`git status` shows `apps/lambda-hello/{pyproject.toml,src/lambda_hello/__init__.py,src/lambda_hello/handler.py}` and `apps/lambda-hello/tests/test_handler.py` deleted from the working tree, uncommitted, while root `pyproject.toml:52-60` still declares:
```
[tool.importlinter]
root_packages = ["core", "lambda_hello", "elevenlabs_agent", "todo_lambda"]
...
forbidden_modules = ["lambda_hello", "elevenlabs_agent", "todo_lambda"]
```
`lambda_hello` is gone from disk but still required by the import-linter contract, so `lint-imports` cannot resolve it and the gate hard-fails. This is not caused by `todo_lambda`'s own code, but it is a real, currently-reproducible failure of a required gate in this repository state, and the TDD log's claim ("`make check` ... import-linter ... pytest — all green", `tdd_01-create-todo.md:101`) does not hold when re-run. Per the hard rule "never approve with a failing gate," this alone blocks approval until either `apps/lambda-hello` is restored/committed or the import-linter contract is updated to drop `lambda_hello` and the deletion is committed.

## Working tree vs. reviewed/logged code — integrity issue

While reviewing, `apps/todo-lambda/src/todo_lambda/features/todos/domain.py` on disk was found to **differ from the committed slice** (`git show HEAD:...domain.py`, commit `eb38272`) and, mid-review, was observed changing between two consecutive reads (first missing a `# type: ignore[arg-type]` comment that later appeared, coinciding with a transient `mypy` failure — "Argument \"title\" to \"Todo\" has incompatible type \"str | None\"; expected \"str\"" — that then cleared). The file has since stabilized (confirmed via two hash checks 3s apart), but the working-tree version now contains a `pydantic.field_validator`-based rewrite of `Todo.create` (before-validator on `title`, a `description` validator, and `try/except PydanticValidationError → ValidationError` translation) that:

- is **not committed** (`git diff HEAD -- .../domain.py` shows the full diff against the logged/committed version),
- has **no corresponding entry** anywhere in `docs/specs/todo-lambda/progress/tdd_01-create-todo.md` — the log's cycles (lines 34-81) describe and match only the simpler, committed `Todo.create` (manual `.strip()`/length checks raising `ValidationError` directly), never the validator-based rewrite.

This means the artifact actually on disk right now is not the artifact the log documents, and no RED/GREEN/REFACTOR entry accounts for the rewrite. That breaks the audit trail TDD logging exists to provide (review criterion 3: "flag production code no test demanded"). Whatever produced this change, it should either be reverted to match the committed/logged state, or committed with a log entry showing what test (if any) motivated it. I evaluated both versions; both pass `make test` as of this review, so this finding is about process/audit-trail integrity, not correctness.

## TDD discipline (cycle-by-cycle, per the log)

The logged cycles (`tdd_01-create-todo.md:34-81`) show genuine RED→GREEN, each tied to a specific scenario, including several honest "passed immediately, no production change" cycles (title+description, empty/whitespace title, server-only fields) rather than padding the log with invented work. The one true escaped-error incident is documented well: raw `pydantic_core.ValidationError` leaking through before `CreateTodoCommand.title` was loosened to `str | None` (`:52-58`). REFACTOR steps are honestly marked "none needed" throughout — no evidence of speculative/gold-plated code beyond what a test demanded, **in the logged version**. The one gap is the undocumented `domain.py` rewrite described above, which the log does not account for at all.

## Architecture / hexagon

- **Domain purity** — `domain.py` is pure Pydantic, no I/O/boto3/AWS; `id` and `created_at` are generated in the use case (`usecases.py:21-24`) and passed in as data, keeping `Todo.create` free of side effects. Correct per `slice-structure.md:15`.
- **Usecases depend on ports, not adapters** — `CreateTodo.__init__(self, repo: TodoRepository)` (`usecases.py:16`) types against the `Protocol`, not `InMemoryTodoRepository`. Correct.
- **Composition root wiring** — `handler.py:9,17` builds the `_repo` singleton once at module scope and constructs `CreateTodo(_repo)` per request inside the routing `handler()`; `create_todo_handler` (the actual handler function) receives an already-built use case (`handlers.py:19`) and never constructs an adapter. Matches `slice-structure.md:23-29` exactly.
- **Cross-slice / reuse ladder** — single slice so far, not yet applicable; no violations.
- **RFC 9457** — `shared/problem.py:7-13` returns `application/problem+json` with `status` + `title`, mapped centrally from `DomainError.status_code` (`shared/errors.py`). Minor: RFC 9457's `title` is meant to be a short, occurrence-invariant summary, while `detail` carries the instance-specific explanation; here the instance-specific message (`"title is required"`) is placed in `title` and no `type`/`detail`/`instance` are emitted. Not a hard violation (`conventions.md:16-18` only requires fields be "derived from the error," and `type` defaults to `about:blank` per the RFC when omitted), but worth tightening before more error variants accumulate in later slices.
- **Observability — missing entirely.** `conventions.md:27-32` requires "Structured JSON logging via `structlog`, built once at cold start" with "one wide, structured line per invocation summarizing the whole request." `handler.py` (the composition root / Lambda entry point) builds no logger and emits no log line, canonical or otherwise — there is no `structlog` (or any logging) anywhere in `todo_lambda`, and `structlog` isn't even a dependency in `apps/todo-lambda/pyproject.toml:6`. Slice 01 is explicitly the walking skeleton that "stands up the full hexagon" (`plan.md:3-7`), and the composition root is exactly where the cold-start logger singleton belongs per `slice-structure.md:27`. This is a real, citable gap against the checked convention, not an out-of-scope item per `project-spec.md`'s Scope section (which doesn't mention logging at all, but doesn't exempt it from the repo-wide convention either).
- **Reuse of `InMemoryTodoRepository` as both adapter and test fake** — sound as far as it goes: since the "real store" for this app *is* in-memory by spec decision, a hand-rolled separate fake would be a near-duplicate of the adapter, and `slice-structure.md:17` calls for adapters "shipped with a hand-rolled in-memory fake" — here they're deliberately the same object, which is a defensible simplification given the persistence decision, not a shortcut around it. The one wrinkle: `InMemoryTodoRepository.todos` (`adapters.py:11-13`) is a public property with no production caller — it exists solely so tests can inspect store contents. That's a test-only concern leaking into the production adapter's public surface; see Test quality below for the consequence.

## Test quality

- Tests invoke the real composition-root `handler.handler` (`test_create_todo.py:5,14`) with synthetic API Gateway proxy events — correct per `conventions.md:25` ("invoke the Lambda `handler`... against the real store").
- Positive-path assertions (`:20-29,35-40,46-48,97-103`) check the HTTP response and body only — correct, through the public surface.
- Negative-path assertions for "no todo is persisted" (`:55,62,69,76,83`) go through `handler_module._repo.todos` — reaching into the composition root's private (underscore-prefixed) module singleton and a test-only adapter property, not through the handler/public read surface. This is exactly what the spec-builder's own testing convention (`agents/skills/spec-builder/SKILL.md:56-60`) asks to avoid: "assert on observable outcomes ... via the public read path ... through the use case's `__call__` or the handler, never adapter internals; tests must survive an internal refactor." As it stands, these five assertions would break under an adapter refactor (e.g., renaming `_repo`, or removing the test-only `.todos` property) even if behavior were unchanged.
  - Given slice 01 has no GET/List endpoint yet (deferred to slices 02/03 per `plan.md:28-50`), there is currently no public read path to assert through, so this is a defensible stop-gap rather than negligence — but it should be revisited once slice 02 lands, and the `.todos` property should not silently become permanent production-adapter surface area.
- Trophy tags — the feature is tagged `@slice-01 @integration` (`01-create-todo.feature:1`) at the feature level; every test is a genuine integration test against the real (in-memory) store via the handler. Correct, no `@unit` scenarios were defined so no unit-test gap exists.
- No mocked-DB middle tier, no assertions on HTTP framework internals, no secrets/`print()` in test or production code. Good.

## Other findings

- `TodoRepository.add` (`ports.py:6-7`) is a generic CRUD-style port method name, contrary to `slice-structure.md:17`'s "Protocols with use-case-driven names (not generic CRUD)". Minor for a one-method port; worth revisiting once more operations land on this port or a sibling port in later slices.

## Required changes

1. **Fix the failing `make imports` gate.** Either restore `apps/lambda-hello` (and commit it) or remove `lambda_hello` from `pyproject.toml`'s `[tool.importlinter]` `root_packages`/`forbidden_modules` (`pyproject.toml:53,60`) and commit the `apps/lambda-hello` deletion consistently. `make check` must be green end-to-end before this slice can ship.
2. **Reconcile the working tree with the logged slice.** `apps/todo-lambda/src/todo_lambda/features/todos/domain.py` on disk does not match commit `eb38272` or `tdd_01-create-todo.md`. Either revert to the committed/logged implementation, or commit the rewrite with a log entry (RED/GREEN/REFACTOR) explaining what motivated it, so the log remains a trustworthy resume cursor and audit trail.
3. **Add cold-start structured logging** (`structlog`, per `conventions.md:27-32`) to `handler.py`, emitting one canonical structured line per invocation (method/path, outcome, `aws_request_id`), before calling this slice's composition root complete.

Non-blocking, worth addressing opportunistically: RFC 9457 field usage (`title` vs `detail`), the `.todos` test-only property's lifecycle once slice 02 lands, and the `add` port method name.

CHANGES_REQUESTED -> docs/specs/todo-lambda/progress/judge_01-create-todo.md (6 findings)
