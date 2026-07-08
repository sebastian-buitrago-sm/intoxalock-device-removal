.PHONY: create-agent sync-agent

# ElevenLabs voice agent CLI. Pass ENV, e.g. `make sync-agent ENV=dev`.
ENV ?= dev

sync-agent:
	uv run agent sync-agent --env $(ENV)
