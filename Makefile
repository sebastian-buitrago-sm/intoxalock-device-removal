.PHONY: install lint format typecheck imports test check synth deploy-lambda deploy-all

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .
	

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy

imports:
	uv run lint-imports

test:
	uv run pytest

# Run every gate the way CI would.
check: lint typecheck imports test

# Infrastructure (all stacks live in infra/; requires the AWS CDK CLI + AWS credentials).
synth:
	cd infra && uv run cdk synth

deploy-lambda:
	cd infra && uv run cdk deploy LambdaHelloStack

deploy-all:
	cd infra && uv run cdk deploy --all
