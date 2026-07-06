# Architecture

**Modular monolith** built on FastAPI. Each feature follows **hexagonal architecture** (ports & adapters) and is **vertically sliced** for isolation — low coupling, high cohesion. Module boundaries extend to the data layer: every module owns a dedicated Postgres schema.

## Philosophy

- Features are self-contained vertical slices. A feature owns its domain, use cases, adapters, handlers, and migrations.
- Inside a feature, dependencies point inward: `handlers → usecases → domain`, with `adapters` implementing ports defined in `usecases`.
- `shared/` is feature-agnostic only. If only one feature uses it, it belongs in that feature.
- ORM is **SQLModel**. Schemas are isolated per module and live **only** in the adapters layer (`features/<module>/adapters/db/`) — never imported from `domain`, `usecases`, or other modules.

## Non-negotiable dependency rules

`A → B` reads "A imports from B." Enforced by `import-linter`.

```
shared/*    →  features/*                          ❌ never
features/A  →  features/B/{domain,usecases,...}    ❌ never  (only features/B/api)
domain/     →  fastapi | sqlmodel | sqlalchemy     ❌ never
usecases/   →  fastapi | sqlmodel | adapters/      ❌ never  (depend on ports)
handlers/   →  adapters/                           ❌ never  (always via deps.py)
adapters/   →  handlers/                           ❌ never
src/*       →  tests/*                             ❌ never
```

Modules **do** talk to each other — only through `features/<other>/api`. That file is the published contract; everything else is private.

If two modules keep reaching past `api.py`, or one `api.py` grows without bound, the boundary is wrong. Merge the modules, or extract the shared concept into its own module or into `shared/`.

## Project Folder Structure 

```
  pyproject.toml
  src/
    app/                      composition root
      __init__.py
      main.py                 create_app, lifespan, registers shared error handlers, loops module.register
    features/                 one package per module
      <module>/
    shared/                   feature-agnostic foundation
      config                  global configurations
      errors                  global domain errors

  tests/
    <module>/unit/...
    <module>/integration/...
    conftest.py
```


## Topic docs

- [module-structure.md](./architecture/module-structure.md) — per-feature template, layer rules, domain/use cases, handlers, DI, settings, app composition.
- [conventions.md](./architecture/conventions.md) — REST, RFC 9457 errors, testing, observability, comments.




