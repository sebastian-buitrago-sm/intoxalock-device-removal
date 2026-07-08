# Agent Instructions — elevenlabs-agent

CLI to manage the "Daisy" ElevenLabs voice agent — an **outbound** agent that
calls a service center to confirm an Ignition Interlock Device removal
appointment.

## Architecture

This sub-project does **not** follow the repo's hexagonal architecture. It is a
**configuration project**: its job is to declare Daisy's ElevenLabs agent
definition (prompt, tools, voice, evaluation) and push it to a target
environment via the ElevenLabs SDK. There is no domain to isolate behind ports
and adapters — the "logic" is the config, and the only I/O is SDK calls. So
there is intentionally no domain/usecases/ports/adapters split and no
import-linter purity contract for this package. Do not add one.

## Layout

```
src/elevenlabs_agent/
  config.py        # Settings: config/<env>.toml + ELEVENLABS_API_KEY from the env
  client.py        # builds the ElevenLabs client from Settings
  definition/       # PURE, env-independent source of truth (prompt, tools, eval, agent config)
  sync/             # create a brand-new agent, or push the definition to an existing one (idempotent)
  calling/          # place a single outbound call
config/             # per-env, NON-secret identifiers (dev.toml, prod.toml)
tests/              # pytest for this app's Python code
tests/agent/        # ElevenLabs conversational tests (simulation + tool-call, run on the platform)
```

## Environments

One definition, two targets. Non-secret, per-environment identifiers
(`agent_id`, `phone_number_id`, webhook URL, `save_tool_id`, concurrency) live
in `config/<env>.toml`; the secret `ELEVENLABS_API_KEY` comes from the environment (a
git-ignored `.env` works — see `.env.example`). Every command selects its
target with `--env`.

> `config/prod.toml` ships with placeholder ids — replace them before running
> any `--env prod` command.

## Usage

```bash
uv run agent create-agent --env dev        # from-scratch: create a new agent, prints its agent_id
uv run agent sync-agent --env dev          # push the definition to the dev agent
uv run agent call --env dev --to +1555... --user-id 123 \
  --slot1 "Mon June 30 5am" --slot2 "Tue July 1 10pm" \
  --make Honda --model Civic --year 2019
```

`create-agent` is a one-time step per environment: it has no `agent_id` to
target yet, so it creates a fresh agent from the definition and prints the new
id. Paste that id into `config/<env>.toml` as `agent_id`, then use
`sync-agent` for every update after that.

Conversational tests are managed under `tests/agent/` — see that folder's
README. Unit tests run with the workspace gates: `make check`.

## Design guidance

- Keep it simple and easy to change. Favor stable seams over churn: functions
  that build the definition take `Settings`, so adding a config value is an
  additive change (new field on `Settings` + a read inside the builder) rather
  than a signature change that ripples through callers and tests.
- Respect SOLID where it earns its keep — but do not add ceremony (ports,
  protocols, extra value objects) that this config project does not need.
- Expose SDK response types directly instead of wrapping them (e.g.
  `TwilioOutboundCallResponse`, `GetAgentResponseModel`); `cast` at the call
  site rather than build a parallel dataclass, since `elevenlabs.*` is
  untyped per mypy config.

## Comments

No comments by default; comment only non-obvious *why*.
