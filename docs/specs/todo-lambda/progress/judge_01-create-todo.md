# Judge verdict — slice 01: Create Todo (re-review)

This is a full, independent re-review from scratch, prompted by commit
`2b05e30` ("refactor(todo-lambda): restructure into nested slice modules and
add observability"), which claims to resolve the three blocking findings from
the prior review (`make imports` failure, an undocumented `domain.py`
rewrite, missing cold-start logging). Not re-litigated on sight per the
task's framing: the in-memory persistence decision (`project-spec.md`
"Decisions" table, row "Persistence") and `InMemoryTodoRepository` doubling
as both production adapter and test fake.

## Baseline read

- `docs/architecture.md`, `docs/architecture/slice-structure.md`, `docs/architecture/conventions.md` (current versions, as modified by `2b05e30`)
- `docs/specs/todo-lambda/features/01-create-todo.feature`
- `docs/specs/todo-lambda/plan.md`, `docs/specs/todo-lambda/project-spec.md`
- `docs/specs/todo-lambda/progress/tdd_01-create-todo.md` (including the new "Post-judge reconciliation" section)
- Source: `apps/todo-lambda/src/todo_lambda/**` (current, nested package layout)
- Tests: `apps/todo-lambda/tests/**` (current, `tests/todos/`, `tests/shared/`)
- `git show eb38272:...` (previously-reviewed committed state) diffed against the working tree, to check what actually changed since the last verdict.

## Scenario → test coverage matrix

| # | Scenario (`01-create-todo.feature`) | Test | Verdict |
|---|---|---|---|
| 1 | Create a todo with only a title | `test_create_todo_with_only_a_title` (`tests/todos/integration/test_create_todo.py:20`) | covered |
| 2 | Create a todo with title and description | `test_create_todo_with_title_and_description` (`:35`) | covered |
| 3 | Title is trimmed before validation | `test_title_is_trimmed_before_validation` (`:46`) | covered |
| 4 | Rejecting a missing title | `test_rejecting_a_missing_title` (`:54`) | covered |
| 5 | Rejecting an empty title | `test_rejecting_an_empty_title` (`:61`) | covered |
| 6 | Rejecting a whitespace-only title | `test_rejecting_a_whitespace_only_title` (`:68`) | covered |
| 7 | Rejecting a title over the length limit | `test_rejecting_a_title_over_the_length_limit` (`:75`) | covered |
| 8 | Rejecting a description over the length limit | `test_rejecting_a_description_over_the_length_limit` (`:82`) | covered |
| 9 | Server-only fields are ignored on create | `test_server_only_fields_are_ignored_on_create` (`:138`) | covered |

All 9 `@scenario`s still have a concrete, 1:1 integration test at their new
location. No coverage gap — this holds after the restructuring.

However, `test_create_todo.py` now has **14** test functions, not 9. Five are
untraceable to any `@scenario`, `.feature`, or the spec (see "New,
unaccounted-for behavior" below): `test_validation_error_is_rfc9457_problem_details`
(`:89`), `test_unmatched_route_is_problem_details` (`:104`),
`test_malformed_json_body_is_bad_request` (`:114`),
`test_non_object_json_body_is_bad_request` (`:124`), and — the serious one —
`test_rejecting_equal_title_and_description` (`:131`).

## Gates — re-run myself, current repo state

- `make lint` — **PASS** (`ruff check .` — all checks passed; `ruff format --check .` — 44 files already formatted).
- `make typecheck` — **PASS** (`mypy` — "Success: no issues found in 44 source files").
- `make imports` — **PASS** (`lint-imports` — "Analyzed 44 files, 63 dependencies... Contracts: 1 kept, 0 broken."). Confirmed `pyproject.toml:53` no longer lists `lambda_hello` in `root_packages`/`forbidden_modules`, and `apps/lambda-hello` is gone from disk and from `git log`/`git show 2b05e30 --stat` (deleted in the same commit, not left dangling). **Prior finding #1 is genuinely fixed.**
- `make test` — **PASS** (27 passed: 8 `test_create_todo.py` core-scenario tests + 6 other `test_create_todo.py` tests + 8 `test_canonical.py` + 3 `test_canonical_logging.py` + 2 `elevenlabs-agent` CLI tests).

All four gates are green, independently re-run just now, not trusted from the log's claim.

## Working tree vs. logged/committed state — audit-trail integrity (still broken, in a new way)

The prior review's finding #2 was: an undocumented rewrite of
`domain.py` from a manual `.strip()`/length-check factory (`Todo.create`,
committed at `eb38272`) to a `pydantic.field_validator`/`model_validator`
implementation, with no RED/GREEN/REFACTOR entry anywhere in the log.

Comparing `eb38272:apps/todo-lambda/src/todo_lambda/features/todos/domain.py`
(the last state the log actually documents, cycle-by-cycle) against the
current `features/todos/domain/todo.py`:

```python
# apps/todo-lambda/src/todo_lambda/features/todos/domain/todo.py:16-25
@field_validator("title", mode="before")
@classmethod
def _trim_title(cls, value: str | None) -> str:
    return (value or "").strip()

@model_validator(mode="after")
def _title_and_description_differ(self) -> "Todo":
    if self.description is not None and self.title == self.description:
        raise ValidationError("title and description must differ")
    return self
```

Two distinct problems here, not one:

1. **The validator-based rewrite itself is still undocumented.** The
   "Post-judge reconciliation" section (`tdd_01-create-todo.md:104-128`)
   describes the commit only as splitting "flat feature modules... into
   per-concern package directories" and adding observability. It does not
   mention that `Todo.create` (a `@classmethod` factory, called from the use
   case) was deleted and replaced by direct `Todo(...)` construction plus
   pydantic validators, called from `CreateTodo.__call__`
   (`features/todos/usecases/create_todo.py:19-30`). That is a real design
   change to the domain layer — not just a file move — and it still has no
   RED/GREEN/REFACTOR cycle anywhere in the log, before or after
   reconciliation. This is the *same* finding as before, not fixed by the
   reconciliation note, only re-described at a coarser grain that omits it.

2. **A brand-new, unspecified business rule was introduced along with the
   rewrite**: `_title_and_description_differ` rejects any create request
   where `title == description`, raising `ValidationError` → `422`. Grepping
   `01-create-todo.feature`, `project-spec.md` (its "Rules & edge cases" 1-9,
   `project-spec.md:100-116`), and `plan.md` for any mention of title/description
   equality returns nothing — this rule does not exist in any spec artifact.
   It is exercised by a new test, `test_rejecting_equal_title_and_description`
   (`test_create_todo.py:131-135`), which is **not** one of the 9
   `@scenario`s and has no corresponding entry in the log's `## Scenarios`
   checklist (`tdd_01-create-todo.md:22-30`) or `## Cycles` section
   (`:32-81`). A client submitting a legitimate request such as
   `{"title": "Fix bug", "description": "Fix bug"}` — a plausible copy/paste
   — is now rejected with a 422 for a reason no one asked for and nothing in
   the project spec justifies. This is production business logic added with
   no test-shaped demand traceable to the agreed spec, which is exactly what
   review criterion 3 ("flag production code no test demanded") exists to
   catch — the fact that a test happens to exercise it does not make it
   spec-driven; the test itself is the undemanded artifact.

Both problems point the same way: the "reconciliation" did not actually
reconcile the log with the code: it renamed/regrouped files (verifiably,
via `git show 2b05e30 --stat`) but the domain rewrite from the *first*
review is still present, unlogged, and has now grown a fabricated rule that
the log also doesn't mention. The log is not a trustworthy resume
cursor/audit trail for the artifact currently on disk.

## New, unaccounted-for behavior beyond the domain rewrite

Beyond the domain layer, the composition root (`handler.py`) and shared
layer gained real production behavior with tests, none of it logged as a
cycle and none of it traceable to a `@scenario`:

- `BadRequest` for malformed/non-JSON-object bodies (`shared/handlers/request.py:5-16`, `handler.py:53-58`), tested by `test_malformed_json_body_is_bad_request` (`:114`) and `test_non_object_json_body_is_bad_request` (`:124`).
- Unmatched-route → 404 problem response (`handler.py:43-52`), tested by `test_unmatched_route_is_problem_details` (`:104`).
- RFC 9457 `errors` extension for per-field pydantic validation failures (`shared/handlers/problem.py:21-25,62-69`), tested by `test_validation_error_is_rfc9457_problem_details` (`:89`).

These three are defensible, architecture-conforming additions (they
implement the composition-root error boundary that `slice-structure.md`
itself was edited, in the same commit, to describe — see below) and none
introduce spec violations the way the title/description rule does. But they
are still net-new production code with no logged RED/GREEN/REFACTOR trail,
in a workflow whose entire premise (per `CLAUDE.md`'s step 3 and this
review's criterion 3) is that the log is the record of what test demanded
what code. A log that silently grows five new tests and several hundred
lines of new production code under a two-sentence "restructuring" summary
is not fulfilling that role, independent of whether the new code is
individually defensible.

## Architecture docs edited inside the same commit

`2b05e30` also modifies `docs/architecture/conventions.md` and
`docs/architecture/slice-structure.md` (see `git show 2b05e30 -- docs/architecture/`),
adding: the 400-on-malformed-body status code, "status codes/methods/paths
are constants," the composition-root "error boundary" bullet, the RFC 9457
five-member-body paragraph, and the "each layer is a package folder... one
file per entity/use case/adapter" structural rule. These edits happen to
match what was just built (the nested package layout, the `routes.py`
constants, the error boundary in `handler.py`, the `type`/`title`/`status`/
`detail`/`instance` body shape). Each change is individually reasonable and
mostly documents/tightens things the *previous* review already flagged
(the RFC 9457 title/detail note was explicitly non-blocking last time).
This is not treated as a blocking finding, but it is worth naming plainly:
the same commit that builds the slice also rewrote the architecture rulebook
the slice is judged against, with no separate record of why. Architecture
docs should be a stable baseline a slice is built and reviewed against, not
something the slice's own implementation commit amends in passing. Going
forward this should go through an explicit, separate architecture-doc change
rather than being folded into a slice's "reconciliation" commit.

## TDD discipline (cycle-by-cycle, per the log)

The originally-logged 9 cycles (`tdd_01-create-todo.md:34-81`) are unchanged
and remain a faithful, honest record of the original build (including the
several "passed immediately, no production change" cycles, and the one
real escaped-`pydantic_core.ValidationError` incident). That part of the
log is still good.

The "Post-judge reconciliation" section (`:104-128`) is not a TDD log entry
in the RED/GREEN/REFACTOR sense — it is a prose summary of a diff, and (per
above) an incomplete one: it omits the domain-layer rewrite, the new
title/description rule, and the four other new tests entirely. Judged
against criterion 3 ("the log shows real RED→GREEN→REFACTOR; flag
production code no test demanded"), this fails for the same underlying
reason the first review failed it, compounded by the new unspecified rule.

## Architecture / hexagon (checked against the new nested layout specifically)

- **Domain purity** — `features/todos/domain/todo.py` imports only `datetime`, `pydantic`, and `shared.domain.errors`; no I/O/boto3/AWS. Still pure per `slice-structure.md:15`, independent of the rewrite's correctness/spec-fidelity problems addressed above.
- **Usecases depend on ports, not adapters** — `CreateTodo.__init__(self, repo: TodoRepository)` (`usecases/create_todo.py:16`) types against the `Protocol` (`ports/todo_repository.py:6-7`), never `InMemoryTodoRepository`. Correct.
- **Composition root wiring** — `handler.py:18-21` builds `_log`/`_repo` singletons once at module scope; `_dispatch` builds `CreateTodo(_repo)` per request and calls `create_todo_handler` (`handler.py:42`), which never constructs an adapter. Matches `slice-structure.md:23-30`.
- **Package-per-layer structure** — `domain/`, `ports/`, `usecases/`, `adapters/`, `handlers/` are each a folder with one file per concern and a re-exporting `__init__.py` (`domain/__init__.py:1-3`, `ports/__init__.py:1-3`, `usecases/__init__.py:1-3`, `adapters/__init__.py:1-3`, `handlers/__init__.py:1-4`), and `shared/` mirrors it (`shared/domain/__init__.py`, `shared/handlers/__init__.py`, `shared/observability/__init__.py`). This is a faithful, mechanical application of the (now-documented) convention — no new dependency-direction violations introduced by the restructuring itself: nothing in `domain/` imports `usecases/`/`adapters/`/`handlers/`; nothing in `shared/` imports `features/`; `handlers/create_todo.py` imports `domain`, `usecases`, and `shared.handlers` only, never `adapters`.
- **Cross-slice / reuse ladder** — still a single slice; not yet applicable.
- **Import-linter contract** — `core is a pure sink` contract still kept (`make imports` output above); the `lambda_hello` root-package entry was correctly dropped alongside the app's deletion, and both the config change and the app deletion are in the same commit (`2b05e30`), so nothing is half-migrated.
- **RFC 9457** — now emits `type`/`title`/`status`/`detail`/`instance`, with `title` correctly the HTTP phrase and `detail` the instance-specific message (`shared/handlers/problem.py:36-41`), addressing the previous review's non-blocking note. Good.
- **Observability** — `handler.py:11-21,24-29` builds `configure_logging()`/`get_logger` once at module scope (cold start) and wraps every dispatch in `canonical_log(...)` (`shared/observability/canonical.py:41-65`), emitting exactly one `request.completed` line per invocation with `aws_request_id`, method, path, route, status, outcome, and duration, and dropping `None` fields. No request bodies/secrets are logged — asserted directly by `test_no_request_body_is_never_logged` (`test_canonical_logging.py:53-60`). This resolves the previous review's finding #3 correctly and is well-tested (`tests/shared/observability/test_canonical.py`, `tests/todos/integration/test_canonical_logging.py`).

## Test quality

- Tests invoke the real composition-root `handler.handler` (`test_create_todo.py:5-6,17`) with synthetic API Gateway proxy events, per `conventions.md`'s testing section. Correct.
- Positive-path assertions check HTTP status/body only, through the public surface. Correct.
- Negative-path "no todo persisted" assertions still reach into `handler_module._repo.todos` (e.g. `test_create_todo.py:58,65,72,79,86,121,128,135`) — the composition root's private, underscore-prefixed module singleton plus a test-only adapter property (`adapters/in_memory_todo_repository.py:11-13`). Same caveat as the prior review: defensible for now since there is no public read endpoint yet (deferred to slice 02), but should be revisited once slice 02 lands, and `.todos` should not become permanent production-adapter surface area purely for test introspection.
- Trophy tags — `@slice-01 @integration` at the feature level; all tests are genuine integration tests through the handler against the real (in-memory) store. Correct.
- No mocked-DB middle tier, no HTTP-framework-internals assertions, no secrets/`print()` anywhere in test or production code (confirmed via the observability code above — logging goes through `structlog`, not `print`).
- Quality concern specific to this re-review: `test_rejecting_equal_title_and_description` (`:131-135`) is a well-formed, passing integration test — but it locks in the fabricated rule described above. A technically well-written test enforcing an unspecified rule is still a defect at the spec-fidelity level, and it is the clearest single piece of evidence that TDD discipline broke down during the "restructuring": someone (or something) added a scenario-shaped test without going through `.feature`/spec authoring.

## Other findings (non-blocking, carried over)

- `TodoRepository.add` (`ports/todo_repository.py:6-7`) is still a generic CRUD-style port method name, contrary to `slice-structure.md:17`'s "use-case-driven names (not generic CRUD)". Minor for a one-method port; revisit once more operations land.
- `InMemoryTodoRepository.todos` (`adapters/in_memory_todo_repository.py:11-13`) remains a test-only public property on the production adapter; see Test quality above.

## Required changes

1. **Remove the fabricated `title != description` rule** (`features/todos/domain/todo.py:21-25`, `_title_and_description_differ`) and its test (`test_create_todo.py:131-135`, `test_rejecting_equal_title_and_description`), or — if this is actually wanted — take it back through `/gherkin-author` to add a `@scenario` to `01-create-todo.feature` and update `project-spec.md`'s "Rules & edge cases" first. Production behavior cannot originate inside a "restructuring" commit with no spec basis.
2. **Reconcile the log with the domain rewrite, for real this time.** `features/todos/domain/todo.py`'s `pydantic.field_validator`/`model_validator`-based implementation (replacing the committed `Todo.create` factory) still has no RED/GREEN/REFACTOR entry anywhere in `tdd_01-create-todo.md`. Add one (or revert to the factory-based implementation the log actually documents), and while doing so, add cycle entries for the other net-new, currently-undocumented tests/production code introduced in `2b05e30`: `test_validation_error_is_rfc9457_problem_details`, `test_unmatched_route_is_problem_details`, `test_malformed_json_body_is_bad_request`, `test_non_object_json_body_is_bad_request`, and the observability tests (which at least have a decent prose description, but no cycle-level RED/GREEN trail either).
3. **Stop editing `docs/architecture/*` from inside a slice's build/reconciliation commit.** If the conventions genuinely need clarifying (the RFC 9457 body-member paragraph, the package-per-layer structure note), do it as its own reviewed change, separate from `todo-lambda`'s slice-01 commit, so the baseline a slice is judged against doesn't move during the slice's own review cycle.

Gates are green (`make lint`, `make typecheck`, `make imports`, `make test`
all pass, independently re-run) and scenario coverage is still 1:1 for all 9
`@scenario`s — the three findings from the *first* review's gate/observability
concerns are genuinely fixed. But this re-review surfaces a new blocking
defect (an unspecified business rule shipped as production code) and finds
that the audit-trail finding from the first review was not actually fixed,
only reworded at a coarser grain. That is still enough to block.

CHANGES_REQUESTED -> docs/specs/todo-lambda/progress/judge_01-create-todo.md (3 findings)
