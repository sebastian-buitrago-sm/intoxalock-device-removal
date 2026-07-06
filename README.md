# intoxalock-removal-device

A Python **monorepo** managed with [`uv` workspaces](https://docs.astral.sh/uv/concepts/workspaces/).
Each app is an independently-deployable package; shared code lives in a `core` library that
both apps import.

```
intoxalock-removal-device/
├── pyproject.toml          # workspace root: members + shared ruff/mypy/pytest/import-linter config
├── packages/
│   └── core/               # shared library (imported as `core`)
├── apps/                   # runtime code only (no infra here)
│   ├── lambda-hello/       # AWS Lambda function
│   └── elevenlabs-agent/   # ElevenLabs SDK CLI (entry point: `hello`)
└── infra/                  # ALL infrastructure for every app (AWS CDK)
    ├── app.py             # single CDK app; instantiates every stack
    └── stacks/
        └── lambda_hello.py # LambdaHelloStack (bundles + deploys apps/lambda-hello)
```

Infrastructure is **centralized** in a top-level `infra/` directory rather than co-located per
app: one CDK `App` declares every stack, so you get a single view of all cloud resources and can
deploy them selectively (`cdk deploy LambdaHelloStack`) or together (`cdk deploy --all`). App
directories under `apps/` hold runtime code only.

## Conventions

- **Package manager:** `uv` (workspace). Each member declares its own `[project]`; apps depend on
  `core` via `[tool.uv.sources] core = { workspace = true }`.
- **Lint / format / imports:** `ruff` (line length 100, `E,W,F,I,B,UP,ANN`).
- **Types:** `mypy --strict` with the `pydantic.mypy` plugin.
- **Architecture boundary:** `import-linter` forbids `core` from importing any app.
- **Tests:** `pytest` (+ `pytest-asyncio` in auto mode).
- **Python:** 3.11.

## Setup

```bash
uv sync          # create the workspace venv, install all members editable
```

## Quality gates

```bash
make check       # ruff + mypy + import-linter + pytest
# or individually:
make lint
make typecheck
make imports
make test
```

## Apps

### ElevenLabs agent CLI

```bash
make run-agent            # -> uv run hello
# Prints "Hello, world!". If ELEVENLABS_API_KEY is set it also probes the SDK.
ELEVENLABS_API_KEY=sk_... uv run hello
```

## Infrastructure

All stacks live in `infra/` (one CDK `App` in `infra/app.py`). Requires the AWS CDK CLI
(`npm i -g aws-cdk`), Docker (for asset bundling), and AWS credentials.

```bash
make synth                # cd infra && uv run cdk synth
make deploy-lambda        # cd infra && uv run cdk deploy LambdaHelloStack
make deploy-all           # cd infra && uv run cdk deploy --all
```

The `LambdaHelloStack` bundles the Lambda by pip-installing `packages/core` + `apps/lambda-hello`
into the function asset, so the shared `core` code ships with the function. Deploying the Lambda and
running the ElevenLabs CLI are fully independent — a change to `packages/core` reaches both on their
next build. As more apps need cloud resources, add a stack under `infra/stacks/` and wire it into
`infra/app.py`.
