# Todo Lambda — Slice Plan

Five vertical slices, one per CRUD operation. Slice 01 is the walking
skeleton: it stands up the full hexagon (domain entity, `TodoRepository`
port, in-memory adapter, handler, composition root, error mapping) for the
simplest operation. Each later slice reuses that skeleton and adds only the
behaviour specific to its operation — no new architectural seams.

Ordering follows create → read (single) → read (list) → update → delete, so
each slice's scenarios can seed data with the store fixture directly rather
than depending on a prior slice's endpoint.

## Slice 01 — Create Todo

`POST /todos`. Builds the walking skeleton: `Todo` domain entity, validation,
`TodoRepository` port + in-memory adapter, `CreateTodo` use case, handler
routing, RFC 9457 error mapping for `422`.

Covers:
- Behaviour: "Creating a todo with a valid `title` persists it and returns
  it with a server-generated `id`, `completed: false`, and server-set
  timestamps."
- Behaviour: "Invalid input ... returns a 422 problem response and persists
  nothing" (create case).
- Rules: 1 (title trim/empty), 2 (length limits), 3 (server-only fields
  ignored), 4 (`completed` ignored on create).

## Slice 02 — Get Todo by id

`GET /todos/{id}`. Adds `GetTodo` use case and the 404 error mapping.

Covers:
- Behaviour: "Fetching a todo by id returns that todo if it exists."
- Behaviour: "Operations on a non-existent id ... return a 404 problem
  response" (get case).
- Rule: 6 (404 on nonexistent id, get case).

## Slice 03 — List Todos

`GET /todos`. Adds `ListTodos` use case, pagination (`limit`/`cursor`),
`completed` filter, and strict param validation.

Covers:
- Behaviour: "Listing todos returns a paginated envelope of todos,
  newest-first by default, optionally filtered ..."
- Behaviour: "Invalid input (... invalid pagination params) returns a 422
  ... " (list case).
- Rules: 7 (strict pagination/filter validation, no clamping), 8
  (newest-first default order).

## Slice 04 — Update Todo (Patch)

`PATCH /todos/{id}`. Adds `UpdateTodo` use case; reuses create's validation
for `title`/`description`.

Covers:
- Behaviour: "Patching a todo by id updates only the fields supplied ...
  and refreshes `updatedAt`; omitted fields are unchanged."
- Behaviour: "Operations on a non-existent id ... return a 404 ..." (patch
  case).
- Behaviour: "Invalid input ... returns a 422 ..." (patch case).
- Rules: 1, 2, 3 (same validation as create, applied to patch), 5 (empty/
  no-op patch is `422`), 6 (404 on nonexistent id, patch case).

## Slice 05 — Delete Todo

`DELETE /todos/{id}`. Adds `DeleteTodo` use case.

Covers:
- Behaviour: "Deleting a todo by id removes it; a subsequent fetch of that
  id returns not-found."
- Behaviour: "Operations on a non-existent id ... return a 404 ..." (delete
  case).
- Rule: 6 (404 on nonexistent id, delete case).

## Coverage map

| Spec item | Slice(s) |
|---|---|
| Behaviour: create persists & returns | 01 |
| Behaviour: list paginated/filtered/ordered | 03 |
| Behaviour: get by id | 02 |
| Behaviour: patch partial update | 04 |
| Behaviour: delete removes | 05 |
| Behaviour: 404 on nonexistent id | 02, 04, 05 |
| Behaviour: 422 on invalid input | 01, 03, 04 |
| Rule 1 — title trim/empty | 01, 04 |
| Rule 2 — length limits | 01, 04 |
| Rule 3 — server-only fields ignored | 01, 04 |
| Rule 4 — `completed` ignored on create | 01 |
| Rule 5 — empty/no-op patch is 422 | 04 |
| Rule 6 — 404 on nonexistent id | 02, 04, 05 |
| Rule 7 — strict pagination/filter validation | 03 |
| Rule 8 — newest-first default | 03 |
| Rule 9 — no compliance constraints | n/a (nothing to test) |

Rule 9 has no scenario — it documents an absence (no auth/PII handling to
verify), not a testable behaviour.
