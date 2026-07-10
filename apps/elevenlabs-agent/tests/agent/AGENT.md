# Agent Instructions — tests/agent

Behavioural tests for the "Daisy" agent, executed on the **ElevenLabs platform**
against a deployed agent (simulation + tool-call scenarios) — not pytest. Full
docs (organization, suite selection, layout) live in `README.md`; this file is
the quick-reference + gotchas for an agent working in this directory.

## Workflow

```bash
uv run agent sync-agent --env dev                                          # push the definition
uv run python apps/elevenlabs-agent/tests/agent/sync_tests.py --env dev    # sync + attach tests
uv run python apps/elevenlabs-agent/tests/agent/run_tests.py --env dev \
  --folder T2_shop_pushback_and_corrections                                # run one suite
```

`sync-agent` must run first when the prompt/tools/evaluation definition
changed — the tests exercise the *live* agent, not the source.

## Gotcha: stale `save_tool_id`

`sync_tests.py` calls `client.conversational_ai.tools.get(tool_id=save_tool_id)`
to mock the `save_call_result` webhook during simulations. `save_tool_id` in
`config/<env>.toml` is a point-in-time snapshot — if that webhook tool is ever
deleted and recreated on the account, the id goes stale and `sync_tests.py`
fails with `ApiError 404 document_not_found`. Fix: read the live agent
(`client.conversational_ai.agents.get(agent_id=...)`), find its
`save_call_result` tool's current id (or check the ElevenLabs dashboard), and
update `save_tool_id` in `config/<env>.toml`.

## Comments

No comments by default; comment only non-obvious *why*.
