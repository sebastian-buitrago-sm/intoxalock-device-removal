# Todo Lambda — Project Spec

## Purpose

A minimal full-CRUD Todo API, deployed as a single AWS Lambda behind API Gateway
(`apps/todo-lambda`). It exists as a simple, self-contained example of the hexagon
pattern described in `docs/architecture.md`: domain + use cases wired to a
swappable persistence port, with an in-memory adapter standing in for a real
store. No authentication, no multi-tenancy — one flat list of todos.

## Actors & context

- **Caller** — any HTTP client hitting API Gateway; unauthenticated.
- **Todo store** — an in-memory adapter behind a persistence port. Data lives only
  for the lifetime of one warm Lambda execution environment: it is lost on cold
  start and not shared across concurrent execution environments. This is an
  accepted limitation of the example, not a defect.

## Behaviour

- Creating a todo with a valid `title` persists it and returns it with a
  server-generated `id`, `completed: false`, and server-set timestamps.
- Listing todos returns a paginated envelope of todos, newest-first by default,
  optionally filtered to only completed or only incomplete todos.
- Fetching a todo by id returns that todo if it exists.
- Patching a todo by id updates only the fields supplied (`title`,
  `description`, and/or `completed`) and refreshes `updatedAt`; omitted fields
  are unchanged.
- Deleting a todo by id removes it; a subsequent fetch of that id returns
  not-found.
- Operations on a non-existent id (get, patch, delete) return a 404 problem
  response.
- Invalid input (bad title/description, empty/invalid patch body, invalid
  pagination params) returns a 422 problem response and persists nothing.

## Contract

REST over API Gateway, Lambda proxy responses. Base path `/todos` (unversioned;
a breaking change would introduce `/v2` per repo convention). All errors are
`application/problem+json` (RFC 9457), mapped from domain errors per
`docs/architecture/conventions.md`.

### Todo representation

```json
{
  "id": "string (server-generated, opaque)",
  "title": "string, 1-200 chars",
  "description": "string, 0-2000 chars, optional (omitted or null when unset)",
  "completed": "boolean",
  "createdAt": "ISO 8601 timestamp",
  "updatedAt": "ISO 8601 timestamp"
}
```

### `POST /todos` — create

- Body: `{ "title": string, "description"?: string }`. Any other field
  (`id`, `completed`, `createdAt`, `updatedAt`) is ignored if present.
- Success: `201`, `Location: /todos/{id}`, body = created todo (`completed: false`).
- Failure: `422` if `title` missing, empty/whitespace-only after trim, or
  >200 chars; or `description` >2000 chars.

### `GET /todos` — list

- Query params (all optional):
  - `completed` — `true` or `false`; filters the list. Any other value is invalid.
  - `limit` — integer, page size. Default `20`, max `100`.
  - `cursor` — opaque pagination cursor from a previous response's `nextCursor`.
- Success: `200`, body:
  ```json
  { "items": [ /* todos, newest-first */ ], "nextCursor": "string | null" }
  ```
- Failure: `422` if `limit` is non-numeric, `<= 0`, or `> 100`; if `cursor` is
  malformed/unrecognized; or if `completed` is present but not `true`/`false`.

### `GET /todos/{id}` — get one

- Success: `200`, body = the todo.
- Failure: `404` if no todo with that id exists.

### `PATCH /todos/{id}` — partial update

- Body: any non-empty subset of `{ "title"?: string, "description"?: string,
  "completed"?: boolean }`. `id`, `createdAt`, `updatedAt` are server-only and
  ignored if present.
- Success: `200`, body = the updated todo, `updatedAt` refreshed.
- Failure:
  - `404` if no todo with that id exists.
  - `422` if the body is empty, contains none of the three patchable fields, or
    a supplied `title`/`description` fails the same validation as create.

### `DELETE /todos/{id}` — delete

- Success: `204`, no body.
- Failure: `404` if no todo with that id exists.

## Rules & edge cases

1. `title` is trimmed before validation; whitespace-only counts as empty → `422`.
2. `title` max 200 chars, `description` max 2000 chars, on both create and patch.
3. Client-supplied `id`, `createdAt`, `updatedAt` are always ignored; the server
   is the sole source of these values.
4. Client-supplied `completed` on create is ignored; every created todo starts
   `completed: false`.
5. A `PATCH` body with zero patchable fields (empty object, or an object with
   only unknown keys) is a `422`, not a no-op `200`.
6. `PATCH`/`GET`/`DELETE` on an id that never existed, or that existed and was
   deleted, returns `404`.
7. List pagination and filter params are validated strictly — no silent
   clamping or fallback. An invalid `limit` (non-numeric, `<=0`, `>100`) or
   unrecognized `cursor` is a `422`, not a best-effort correction.
8. `GET /todos` defaults to newest-first order when no explicit sort is
   requested (no sort param is defined in this version).
9. No compliance/eligibility constraints apply (no auth, no PII beyond
   free-text `title`/`description`).

## Scope

**In scope:**
- Domain, use cases, ports, and an in-memory adapter for full CRUD on a Todo.
- The Lambda handler (composition root) parsing API Gateway proxy events and
  mapping to/from the above HTTP contract.
- Unit tests (use cases against the in-memory fake) and integration tests
  (handler invoked with synthetic API Gateway events against the in-memory
  adapter).

**Out of scope (this pass):**
- Authentication, authorization, and multi-tenancy (single flat list, all
  callers share it).
- A durable persistence adapter (DynamoDB or otherwise) — the in-memory
  adapter is the only implementation for now; swapping it in later is a
  drop-in adapter change, not a domain/use-case change.
- `infra/` CDK wiring (API Gateway + Lambda stack) — deferred as separate,
  mechanical follow-up work once the slice exists, mirroring how
  `LambdaHelloStack` was added.
- Any endpoint or field beyond what's listed above (no due dates, priority,
  tags, bulk operations, or sorting other than newest-first).

## Decisions

| Decision | Chosen | Rejected alternatives |
|---|---|---|
| Tenancy/auth | Single-user, no auth | Multi-user with per-caller ownership — deferred as a separate future slice rather than reshaping the domain now |
| Persistence | In-memory adapter (example-only) | DynamoDB/real store — explicitly deferred; port/adapter boundary makes the swap independent of domain/use cases |
| Todo fields | `id`, `title`, `description`, `completed`, `createdAt`, `updatedAt` | Adding due date/priority/tags — out of scope for "pretty simple" |
| List shape | Paginated envelope (`items` + `nextCursor`) | Bare array — rejected, contradicts repo-wide convention in `docs/architecture/conventions.md` |
| Update verb | `PATCH` (partial) | `PUT` (full replace) — rejected as less natural for toggling a single field like `completed` |
| List page size | Client-configurable `limit`, default 20, max 100 | Fixed page size — rejected as needlessly rigid for a query param this cheap to support |
| List filter | `?completed=true\|false` supported | No filter — rejected, trivial to support and clearly useful for a todo list |
| List default order | Newest-first | Oldest-first (insertion order) — rejected, newest-first is the more useful default |
| Create/patch validation limits | `title` ≤200 chars, `description` ≤2000 chars; server-only fields silently ignored rather than rejected | Rejecting requests that include server-only fields — rejected as needless friction for clients that round-trip a full object |
| Empty/no-op `PATCH` | `422` | Silent `200` no-op — rejected, a no-op success masks client bugs (e.g. a typo'd field name) |
| Infra wiring | Out of scope for this spec | Include `LambdaHelloStack`-style CDK stack now — deferred; behavior should be specified and buildable independent of deployment plumbing |
| Invalid pagination params (`limit`, `cursor`) | Reject strictly with `422` | Forgiving clamp/fallback — rejected, consistent with the repo's existing `ValidationError`→422 convention and avoids masking client bugs |
| App/package name | `apps/todo-lambda` (package `todo_lambda`) | — |

## Open questions

None — all decisions above were resolved during spec review.
