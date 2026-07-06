# Architecture

**`uv`-workspace monorepo.** Runtime code splits into **apps** (each a deployable — usually one AWS Lambda behind API Gateway) and **packages** (shared libraries). Every app is internally a **hexagon** (ports & adapters), **vertically sliced** into features. Infrastructure for the whole repo is centralized in `infra/` (AWS CDK).

## Terminology

- **app** — one deployable under `apps/`; holds one or more slices.
- **package** — a shared library under `packages/`, imported by apps; a pure sink.
- **slice** — a vertical feature inside an app (`features/<slice>/`); owns its domain, use cases, adapters, handlers, and data.
- **app-local `shared/`** — feature-agnostic code shared across slices *within one app*.

## Reuse ladder

Promote code outward only on real demand: a slice's own code → app-local `shared/` (2+ slices need it) → a `packages/*` library (2+ apps need it).

Share deliberately: shared code couples its consumers, so promote only what is a genuine, stable abstraction. Prefer a little duplication over the wrong abstraction.

## Dependency rules

`A → B` reads "A imports from B." Enforced by `import-linter`.

Across the workspace:
```
packages/*  →  apps/*        ❌  packages are pure sinks
apps/A      →  apps/B        ❌  apps never import each other
packages/B  →  packages/A    ✅  only when declared (no cycles)
apps/*      →  packages/*    ✅
```

Apps share behavior through a package, never by importing a sibling app.

Inside an app, dependencies point inward (`handlers → usecases → domain`, `adapters` implement ports):
```
features/A  →  features/B internals   ❌  only via features/B/api
shared/     →  features/*             ❌  app-local shared stays feature-agnostic
domain/     →  boto3 | AWS | frameworks   ❌  domain is pure
usecases/   →  adapters/ | boto3      ❌  depend on ports
handlers/   ↔  adapters/              ❌  wired only in the composition root
```

Slices talk only through `features/<other>/api`. If two slices keep reaching past `api.py`, the boundary is wrong — merge them or promote the shared concept.

## Topic docs

- [slice-structure.md](./architecture/slice-structure.md) — the hexagon inside an app: layers, composition root, persistence.
- [conventions.md](./architecture/conventions.md) — REST over API Gateway, RFC 9457 errors, testing, observability.
