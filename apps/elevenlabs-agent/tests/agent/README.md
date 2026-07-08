# Agent conversational tests

These are the agent's behavioural tests, executed on the **ElevenLabs platform**
against a deployed agent (simulation + tool-call scenarios). They are separate
from the pytest suite one directory up, which tests this project's own Python.

They are standalone scripts (not collected by pytest) and pick their target
agent from the environment config, exactly like the CLI:

```bash
# 1. Push the agent definition first (tests run against the live agent).
uv run agent sync-agent --env dev

# 2. Create/update the test definitions AND attach them to the agent (idempotent).
uv run python apps/elevenlabs-agent/tests/agent/sync_tests.py --env dev

# 3. Run them and print the verdicts.
uv run python apps/elevenlabs-agent/tests/agent/run_tests.py --env dev
```

The test definitions live at the workspace (account) level — that is the only
place ElevenLabs stores them. Because they are written specifically for Daisy
(they reference her `save_call_result` tool), step 2 also **attaches** them to
the env's agent so they appear under the agent's Tests tab and run against it.

`sync-agent` reads the agent's currently attached test ids before pushing the
definition, so it preserves attachments made by `sync_tests.py` regardless of
run order.

`sync_tests.py` targets the `save_call_result` tool via `save_tool_id` from
`config/<env>.toml`; keep that in sync when the webhook tool is recreated.

## Layout

```
scenarios.feature   # design-time catalog: every scenario + its ID (@T1-1, @E-3, ...)
sync_tests.py       # orchestrator: registers suites in SUITES, syncs them (idempotent)
run_tests.py        # runs every test in the account against the env's agent
suites/             # one module per suite (mirrors scenarios.feature)
  shared.py         # concrete dynamic-variable values + the exact() helper
  t1_core_happy_paths.py   # build(save_tool_id) -> list[TestsCreateRequestBody]
```

Each suite module exposes `build(save_tool_id)` and each test points back to its
scenario by ID (e.g. `scenarios.feature @T1-1`) — search that tag in
`scenarios.feature` to read the full Gherkin. Add a suite by creating a module in
`suites/` and registering its `build` in `SUITES` in `sync_tests.py`.
