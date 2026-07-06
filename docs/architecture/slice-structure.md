# Slice structure

A slice is a vertical feature inside an app — one per business capability, self-contained. An app holds one or more slices; code shared between them moves to the app-local `shared/`.

## Layers

Dependencies point inward; `domain` is a sink.

```
handlers → deps → usecases → ports ← adapters
                     ↓
                  domain
```

- **domain** — entities, value objects, errors. Pure Python + Pydantic; no I/O, `boto3`, AWS types, or frameworks. Validators enforce business invariants only. Errors inherit shared bases so the error mapper renders them to HTTP.
- **usecases** — one business operation per callable class. Takes ports as dependencies, returns domain results, raises domain errors (never HTTP/AWS). Inputs are frozen command/query models.
- **ports** — `Protocol`s with use-case-driven names (not generic CRUD), each shipped with a hand-rolled in-memory fake.
- **adapters** — port implementations: data-store repositories, external service clients.
- **handlers** — the API Gateway inbound adapter: parse the proxy event → build command → call use case → map result (or domain error) to a `{statusCode, body}` response. No business logic.

Slices expose a public surface (`api.py`) for other slices; everything else is private.

## Composition root

Each app's Lambda entry point is also its composition root — the only place that wires adapters to use cases.

- **Cold-start singletons** (config, data-store clients, HTTP pools, logger) are built once at module scope and reused across warm invocations.
- **Routing** maps the event `(method, path)` to a slice handler.
- **Per-request**: build use cases from ports (reusing the singletons) and dispatch. Handlers receive fully-built use cases — they never construct adapters.

## Persistence

The store (DynamoDB by default, but any DB/cache/API) lives entirely behind ports and adapters.

- A slice owns its store; only its adapters know the schema and driver. Domain and use cases never see raw records.
- Connection details reach the slice via env var; provisioning is an infra concern, not the slice's.
- A slice's data is private — cross-slice reads go through the other slice's `api.py`.

## Settings

Read from the environment, scoped per slice, and promoted to app-local `shared/` (or a package) as more consumers appear. Validated at cold start to fail fast.
