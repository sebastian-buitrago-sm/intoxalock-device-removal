# Agent Instructions

## Workflow

Spec-driven, one vertical slice at a time. Each step hands off to the next:

1. **`/spec-partner`** (skill) — refine a requirement into an agreed, testable spec → `docs/specs/<feature>/project-spec.md`.
2. **`/gherkin-author`** (skill) — slice it into vertical slices (`plan.md`) and author the `.feature` contracts. Approve the slice plan before scenarios.
3. **`/spec-builder`** (skill) — TDD-build one slice from its `.feature`, following `docs/architecture`; logs each cycle to `docs/specs/<feature>/progress/tdd_<slice>.md`; gates on `make check`.
4. **`judge-iteration`** (subagent) — independently review the slice (coverage, TDD discipline, hexagon boundaries, gates) → `docs/specs/<feature>/progress/judge_<slice>.md`.

Sources live in `agents/{skills,agents}/`, symlinked into `.claude/`.

## Comments

- No comments by default; prefer self-explanatory code.
- Comment only non-obvious *why*: complex logic, tricky algorithms, subtle edge cases.


