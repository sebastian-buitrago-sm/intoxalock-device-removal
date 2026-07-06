# Conventions

## Comments

- Comment **complex logic** and **non-trivial decisions** only.
- Do not comment self-evident code, type signatures, or what a function does (the name does that).

## REST

- Plural nouns; nest only for true parent/child ownership. Prefer query filters over deep paths.
- **Lists** return `ListEnvelope[T]` from `shared/http/pagination.py` — never a bare array.
- **Pagination**: cursor-based (`?cursor=&limit=`), default `limit=20`, `max_limit=100`. Cursor is opaque.
- **Filter** with typed query params bound to a Pydantic `<Entity>Filter`. **Search** is a separate use case behind `?q=`. Do not combine.
- **Versioning**: additive by default; new `/v<n+1>` only for breaking changes. Deprecated routes emit a `Deprecation` header.
- Status codes follow REST: 201+`Location` on create, 204 on delete, 409 on conflict, 422 on validation, 429+`Retry-After` on rate limit.

## Errors — RFC 9457

All error responses use `application/problem+json` and the shared `Problem` model.

- Domain errors inherit shared bases mapped centrally in `shared/http/error_handlers.py`:
  `NotFoundError`→404, `ConflictError`→409, `ValidationError`→422, `UnauthorizedError`→401, `ForbiddenError`→403.
- Default `Problem` fields are derived: `type` from class name (kebab-case), `title` from docstring/class name, `detail` from `str(exc)`, `instance` from request path.
- Per-feature `handlers/error_map.py` exists only for non-standard mappings (custom status, headers, extension fields); `register(app)` wires it.
- `RequestValidationError` is reshaped into a `Problem` (`status=422`, `type="validation-error"`) with an `errors` extension listing field paths.

## Testing

Two tiers; test behavior, not implementation, test should verify  be resilient to changes and act as security net for changes.

- **Unit** (`tests/<module>/unit/`) — use cases and complex domain logic, with in-memory fakes.
- **Integration** (`tests/<module>/integration/`) — full FastAPI app against real Postgres via testcontainers.
- No mocked-DB middle tier.
- Assert on outcomes (return values, errors, persisted state, HTTP responses), never internals.
- Cover each use case's happy path + domain errors, each handler's contract, authorization, and cross-module composition. Skip trivial getters and Pydantic-enforced invariants.

### Naming

- **Unit tests** — name reflects the capability under test (use-case-shaped). Form: `test_<verb>_<noun>_<scenario>`.
  - `test_create_invoice_rejects_duplicate_external_id`
  - `test_settle_invoice_marks_status_paid_when_amount_matches`
- **Integration tests** — phrased as an EARS (Easy Approach to Requirements Syntax) requirement. The two forms you'll use most:
  - **Event-driven**: `test_when_<event>_<endpoint>_shall_<response>`
    - `test_when_principal_is_admin_post_invoices_shall_return_201_with_location`
  - **Unwanted behavior**: `test_if_<unwanted>_<endpoint>_shall_<response>`
    - `test_if_external_id_duplicates_post_invoices_shall_return_409`

## Observability

Logging is structured via `structlog` (JSON in prod, console in dev). injected via `Depends`.

- Request context (`request_id`, actor, tenant) is bound by middleware; use cases add operation fields.
- Event names are lowercase dotted snake_case (`<domain>.<action>[.<outcome>]`); data goes in fields, not the message.
- No secrets, auth headers, raw bodies, or `print()` in logs.
- `request_id` propagates as `X-Request-ID` on outbound calls.
