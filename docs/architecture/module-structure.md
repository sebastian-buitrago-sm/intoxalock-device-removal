# Module structure

A module is a vertical slice — one per business capability. Self-contained: domain, use cases, adapters, handlers, migrations, public surface.

## Directory template

```
features/<module>/
  __init__.py        # register(app: FastAPI) -> None
  api.py             # public surface for other modules
  config.py          # module-scoped settings (optional)
  deps.py            # Depends factories + Annotated aliases
  routes.py          # APIRouter assembly
  domain/            # entities, value objects, errors
  usecases/
    ports/           # Protocol declarations + in-memory fakes
    ...              # one use case per file
  adapters/          # port implementations (db/, external services)
  handlers/          # FastAPI routes, request/response schemas, error mapping
  migrations/        # alembic
```

## Dependency arrows

```
handlers/ → deps.py → usecases/ → ports/ ← adapters/
                          ↓
                       domain/
```

`handlers/` never reaches `adapters/` directly. `domain/` is a sink.

## Domain

Pure Python (stdlib + Pydantic). No I/O, no framework.

- **Entities** (`domain/entities.py`): Pydantic `BaseModel` with `frozen=True, extra="forbid"`. Validators enforce business invariants only — not wire formatting or serialization.
- **Value objects** (`domain/value_objects.py`): `Annotated` types with `AfterValidator`. Cross-module ones live in `shared/domain/types.py`. Use a class only when behavior is attached (e.g. `Money.add()`).
- **Errors** (`domain/errors.py`): inherit from shared bases (`NotFoundError`, `ConflictError`, `ValidationError`, `UnauthorizedError`, `ForbiddenError`) so the shared HTTP handler maps them automatically. No status codes in domain.

## Use cases

One business operation = one callable class = one file.

- Class `<Verb><Noun>`; file matches.
- `__init__` takes ports as keyword-only args.
- `async def __call__(self, cmd)` returns the domain result.
- Raises domain errors — never `HTTPException`.
- **Commands/Queries**: frozen Pydantic models in `usecases/commands.py`. Carry `Principal` as a field when the actor matters. Handlers, workers, and CLIs all construct the same command.
- **Ports** (`usecases/ports/<name>.py`): `typing.Protocol`, async, use-case-driven method names — not generic CRUD.
- **Fakes** (`usecases/ports/_fakes.py`): hand-rolled in-memory fakes, shipped with the module. No `AsyncMock`.

## Does NOT belong inside the hexagon

HTTP types, SQLModel/SQLAlchemy, settings/env reads, logging config, try/except around infrastructure errors.

## Handlers

Thin: validate request → build command → call use case → map result. No business logic.

- One `APIRouter` per module: prefix `/v<n>/<plural-noun>`, tags `[<module>]`, router-level `Depends(get_current_principal)`. Public routes (health, login, webhooks) use a separate unauthenticated router.
- **Schemas** (`handlers/schemas.py`): Pydantic with `extra="forbid"` for requests. Only define when wire shape ≠ domain shape; otherwise return the entity directly. Naming: `<Verb><Noun>Request`, `<Noun>Response`.
- **HTTPException** may be raised only here; use cases raise domain errors.

REST and error conventions live in [conventions.md](./conventions.md).

## Composition (`deps.py`)

The only file that imports both `usecases/` and `adapters/`. May import `usecases/`, `adapters/`, `domain/`, `shared/`, and other modules' `api.py`. Never imports `handlers/`.

- One `Depends` factory per port implementation, one per use case.
- Each factory has a matching `<UseCase>Dep` / `<Port>Dep` = `Annotated[T, Depends(factory)]`.
- Handlers depend on the alias, never on a port directly.

Scopes: singletons (settings, DB engine, HTTP client pool, logging) are built once in `lifespan`. Sessions, repositories, use cases, and `Principal` are request-scoped via `Depends`.

## Settings

- Module-scoped settings live in `features/<module>/config.py` with `env_prefix="<MODULE>_"`, exposed via an `@lru_cache` factory.
- A setting consumed by 2+ modules graduates to `shared/config.py`.
- `create_app` calls every settings factory once at startup to fail-fast.

## App assembly

Each module's `__init__.py` exposes `register(app: FastAPI) -> None` that includes its router(s) and any module-specific error handlers or lifespan hooks. `register` must be order-independent; modules do not talk to each other at registration time.

`app/main.py` builds the app in this order:

1. Install middleware (request id, logging, CORS, timing).
2. Register shared error handlers (domain base classes → Problem responses).
3. Call `module.register(app)` for each module (module-specific handlers win for their subclasses).

Settings validation and engine init happen inside `lifespan`.

## New module checklist

1. `__init__.py` exposes `register(app)`.
2. `routes.py` defines an `APIRouter` with prefix, tags, and auth dependency.
3. Scaffold `domain/`, `usecases/ports/`, and `adapters/` together — never one alone.
4. Every port has a fake from day one.
5. `deps.py` exposes a factory + `Annotated` alias per use case.
6. Initialize `migrations/` against the module's schema (see [persistence.md](./persistence.md)).
7. Add the module to import-linter contracts and `app/main.py`.
