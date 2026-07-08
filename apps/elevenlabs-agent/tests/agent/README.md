# Agent conversational tests

These are the agent's behavioural tests, executed on the **ElevenLabs platform**
against a deployed agent (simulation + tool-call scenarios). They are separate
from the pytest suite one directory up, which tests this project's own Python.

They are standalone scripts (not collected by pytest) and pick their target
agent from the environment config, exactly like the CLI:

```bash
# 1. Push the agent definition first (tests run against the live agent).
uv run agent sync-agent --env dev

# 2. Create/update the test definitions in the account (idempotent).
uv run python apps/elevenlabs-agent/tests/agent/create_tests.py --env dev

# 3. Run them and print the verdicts.
uv run python apps/elevenlabs-agent/tests/agent/run_tests.py --env dev
```

`create_tests.py` targets the `save_call_result` tool via `save_tool_id` from
`config/<env>.toml`; keep that in sync when the webhook tool is recreated.
