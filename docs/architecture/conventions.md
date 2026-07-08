# Conventions

## Comments

Comment non-obvious *why* only — complex logic or non-trivial decisions. Never narrate what the code does.

## Function signatures

Past 2 arguments, favor connascence of name over connascence of position: make the extra parameters keyword-only (`*`) so call sites pass them by name and can't be broken by silently reordering same-typed arguments (e.g. swapping `vehicle_make`/`vehicle_model`).

## REST (over API Gateway)

Handlers emit Lambda proxy responses (`{statusCode, headers, body}`).

- Plural nouns; prefer query filters over deep paths.
- **Lists** return a paginated envelope (never a bare array) with an opaque cursor.
- REST status codes: 201+`Location` on create, 204 on delete, 400 on a malformed body, 409 on conflict, 422 on validation.
- Status codes, methods, and paths are constants (`http.HTTPStatus`/`HTTPMethod`, a slice `routes.py`), never literals.
- **Versioning** is additive; a new `/v<n+1>` only for breaking changes.

## Errors — RFC 9457 Problem Details

Every error response is `application/problem+json`, rendered at a **single boundary in the composition root** — validation (422), malformed body (400), unknown route (404), and unexpected failures (500) all map there. Handlers and use cases only raise; they never format errors.

Domain errors are a pure taxonomy (`DomainError` + subclasses) carrying **no** HTTP knowledge. A type→status map in the HTTP adapter (`shared/handlers/problem.py`) assigns the code (`ValidationError`→422 today; `NotFoundError`→404, `ConflictError`→409, etc. as slices need them). A raised `pydantic.ValidationError` is treated as 422 alongside them.

Bodies carry the five standard members — `type`, `title`, `status`, `detail`, `instance`. With `type` `about:blank`, `title` is the HTTP status phrase and `detail` the specific message. Extension members (`errors` for per-field validation, `traceId`) are additive and optional.

## Testing

Test behavior, not implementation. Assert on outcomes (returns, errors, persisted items, responses), never internals.

- **Unit** — use cases and domain logic, with in-memory fakes. Fakes cover logic only.
- **Integration** — invoke the Lambda `handler` with a synthetic API Gateway event against the real store (e.g. DynamoDB Local / `moto`). Store-specific semantics are covered only here. No mocked-DB middle tier.

## Observability

Structured JSON logging via `structlog`, built once at cold start (`configure_logging()`/`get_logger()` in `shared/observability`).

- Bind request-scoped context (`aws_request_id`, `http_method`, `path`, ...) with `structlog.contextvars.bind_contextvars` at the top of the composition root, and `clear_contextvars()` in a `finally` so nothing leaks into the next warm-container invocation. Bound context rides along on every log call without threading a logger through use cases.
- Log fields as keyword arguments on the call site (`log.info("request_completed", status_code=..., route=...)`); no derived-outcome or log-level abstraction on top of `structlog`.
- No secrets, auth headers, raw bodies, or `print()`. Propagate the request id as `X-Request-ID` on outbound calls.
