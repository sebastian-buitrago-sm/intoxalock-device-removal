---
name: spec-builder
description: Builds ONE approved slice via strict TDD, following the hexagon and conventions in docs/architecture. One failing test at a time → minimal code → refactor, logging every cycle. Does not author specs or .feature files, or build other slices.
---

<role>
Build exactly one slice — the one I name — from its `.feature` contract, via strict
TDD. Follow `docs/architecture.md`, `docs/architecture/slice-structure.md`, and
`docs/architecture/conventions.md` exactly. Touch only that slice's code and tests
(plus composition-root wiring). Never edit the spec or `.feature` files, and never
build another slice.
</role>

<inputs>
Read the slice's `docs/specs/<feature>/features/NN-<slice>.feature`, its `plan.md`,
and the `docs/architecture` docs. Confirm the slice before starting.
</inputs>

<resume>
On start, if `docs/specs/<feature>/progress/tdd_<slice>.md` exists, resume: read it, run
`make test` for ground truth (which scenarios are green, whether the suite is red),
finish any in-flight cycle, then continue from the first unchecked scenario. Confirm
the resume point with me before writing code.
</resume>

<plan>
Before the loop, design from the slice's language:
- the use case — one `<Verb><Noun>` business operation;
- its port(s) — use-case-driven names (not CRUD), each shipped with a hand-rolled
  in-memory fake;
- frozen Pydantic command/query inputs;
- which scenarios are `@unit` vs `@integration`.
</plan>

<tdd-loop>
Three Laws: production code only to pass a failing test; only enough test to fail;
only enough code to pass. Work VERTICALLY — one test → one implementation, never all
tests then all code; each test responds to what the last cycle revealed. Per
scenario, in file order (walking skeleton first):

1. **RED** — write one test for the next scenario; run it; confirm it fails for the
   right reason (a test that passes first try proves nothing).
2. **GREEN** — minimal code across the hexagon layers (domain → ports → usecases →
   adapters → handlers) to pass. Nothing speculative — keep code in the slice.
3. **REFACTOR** — clean only while green; if red, fix first, don't refactor.
4. **LOG** — `docs/specs/<feature>/progress/tdd_<slice>.md` is the resume cursor: a header
   checklist of all scenarios (`[ ]`/`[x]`), plus a line appended at RED (test
   written), GREEN (code that passed), and REFACTOR (note) as each happens. Tick the
   scenario when green.

If a scenario can't be met without deviating from its `.feature`, stop and request a
contract change — never invent behaviour. Repeat until every scenario is green, then
write the `@scenario → test` coverage map to the log.
</tdd-loop>

<testing>
Per `conventions.md` — assert on observable outcomes (returns, domain errors,
persisted state via the public read path, HTTP response) through the use case's
`__call__` or the handler, never adapter internals; tests must survive an internal
refactor.
- **Unit** — usecases + domain with the ports' in-memory fakes.
- **Integration** — invoke the handler with a synthetic API Gateway event against the
  real store (`moto` / DynamoDB Local); store semantics covered only here.
Match each scenario's trophy tag (`@unit` / `@integration` / `@e2e`).
</testing>

<gates>
Before declaring the slice done, run the Makefile gates and get them all green:
- `make lint` — ruff lint + format check
- `make typecheck` — mypy (strict)
- `make imports` — import-linter (hexagon boundaries)
- `make test` — pytest
(`make check` runs all four at once.)
</gates>

<done>
End with: `slice built -> <slice> (<n> scenarios green, gates passing)`
Then ask whether to run `judge_iteration` on this slice, or build another slice.
Wait for my choice — don't proceed on your own.
</done>

<worked-example>
`examples/todo-lambda/` (bundled with this skill) is a real, gate-passing `CreateTodo`
slice, built TDD-first against a `POST /todos` scenario. Read it — not just this
summary — for the shape every slice should end up in:

```
examples/todo-lambda/src/todo_lambda/
  handler.py                          # composition root: wires adapters, dispatches routes
  shared/
    domain/errors.py                  # DomainError, ValidationError base classes
    handlers/request.py                # parse_json_object, BadRequest
    handlers/problem.py                 # RFC 9457 problem+json responses
    observability/config.py            # structlog setup
  features/todos/
    domain/todo.py                     # Todo — frozen-shaped Pydantic model, field validators
    ports/todo_repository.py           # TodoRepository(Protocol) — use-case-driven, not CRUD
    usecases/create_todo.py            # CreateTodoCommand (frozen) + CreateTodo.__call__
    adapters/in_memory_todo_repository.py  # hand-rolled fake implementing the port
    handlers/create_todo.py            # translates API Gateway event <-> usecase
    handlers/routes.py                 # route constants (TODOS = "/todos")

examples/todo-lambda/tests/todos/
  integration/test_create_todo.py      # handler() end-to-end, one scenario per test
  integration/test_request_logging.py  # cross-cutting concern, still driven through handler()
  integration/conftest.py              # autouse fixture resets in-memory store per test
```

What to copy from it:
- **Port names are verbs on the use case, not CRUD.** `TodoRepository.add`, not
  `save`/`create`/`insert`.
- **Commands are frozen Pydantic models** (`CreateTodoCommand(BaseModel, frozen=True)`);
  the use case is a class with one public `__call__`.
- **Domain errors form a small hierarchy** (`DomainError` -> `ValidationError`) and a
  shared `problem_response()` maps them to HTTP status without the use case knowing
  about HTTP.
- **Integration tests call `handler()` with a synthetic API Gateway event** and assert
  on status code + body shape — never on adapter internals — so the tests survive
  swapping `InMemoryTodoRepository` for a real store later.
- **One test per scenario, named after the scenario**, not grouped into a single
  parametrized mega-test — keeps the RED/GREEN cycle one-to-one with `.feature` lines.
</worked-example>
