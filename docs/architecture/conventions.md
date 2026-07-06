# Conventions

## Comments

Comment non-obvious *why* only — complex logic or non-trivial decisions. Never narrate what the code does.

## REST (over API Gateway)

Handlers emit Lambda proxy responses (`{statusCode, headers, body}`).

- Plural nouns; prefer query filters over deep paths.
- **Lists** return a paginated envelope (never a bare array) with an opaque cursor.
- REST status codes: 201+`Location` on create, 204 on delete, 409 on conflict, 422 on validation.
- **Versioning** is additive; a new `/v<n+1>` only for breaking changes.

## Errors — RFC 9457 Problem Details

All error responses use `application/problem+json`. Domain errors inherit shared bases mapped centrally to status codes (`NotFoundError`→404, `ConflictError`→409, `ValidationError`→422, `UnauthorizedError`→401, `ForbiddenError`→403); `Problem` fields are derived from the error.

## Testing

Test behavior, not implementation. Assert on outcomes (returns, errors, persisted items, responses), never internals.

- **Unit** — use cases and domain logic, with in-memory fakes. Fakes cover logic only.
- **Integration** — invoke the Lambda `handler` with a synthetic API Gateway event against the real store (e.g. DynamoDB Local / `moto`). Store-specific semantics are covered only here. No mocked-DB middle tier.

## Observability

Structured JSON logging via `structlog`, built once at cold start.

- **Canonical logs**: emit one wide, structured line per invocation summarizing the whole request — bound context (`aws_request_id`, actor, tenant), the operation, and its outcome — instead of scattering many small logs.
- No secrets, auth headers, raw bodies, or `print()`. Propagate the request id as `X-Request-ID` on outbound calls.
