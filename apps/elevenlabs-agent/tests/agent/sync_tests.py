"""Create (or update) the ElevenLabs agent tests for Daisy.

These are the agent's *conversational* tests (simulation + tool-call), run on
the ElevenLabs platform against the deployed agent — distinct from the pytest
suite one level up, which covers this project's own Python code.

Tests are organized into suites under suites/, one module per suite, mirroring
scenarios.feature (T1..T4 tiers, E edge cases, NS needs-spec). Each suite module
exposes build(save_tool_id) -> list[TestsCreateRequestBody]; register a new suite
in SUITES below, pairing its build with the ElevenLabs folder its tests live in.

Each suite's tests are placed in a same-named folder in the account, so the
dashboard groups them and run_tests.py can select a whole suite with --folder.

Idempotent: within its folder each test is looked up by name and updated if it
exists, otherwise created — so re-running never produces duplicates. Which agent
(and which save_call_result tool id) it targets is chosen by --env.

After syncing, the tests are attached to the env's agent (via sync_agent) so
they surface under the agent's Tests tab and run against it. `agent sync-agent`
preserves existing attachments, so sync order does not matter.

Run with:  uv run python apps/elevenlabs-agent/tests/agent/sync_tests.py --env dev
"""

import argparse
from collections.abc import Callable
from dataclasses import dataclass

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.tests.types import TestsCreateRequestBody
from elevenlabs.types import ToolRequestModel
from elevenlabs_agent.client import build_client
from elevenlabs_agent.config import Settings, load_settings
from elevenlabs_agent.sync.agent_sync import sync_agent
from suites import t1_core_happy_paths

SuiteBuilder = Callable[[str], list[TestsCreateRequestBody]]

# Canned success the simulations see when they mock save_call_result by id. Empty
# parameter_conditions means the mock always activates. This lives here, not in the
# production agent definition, because it is test-only: real calls always hit the
# webhook. Without it a "mocked" webhook tool has no return value and falls through to
# the live endpoint, whose errors trip the prompt's retry/give-up path and fail the sims.
SAVE_TOOL_MOCK_RESULT = '{"success": true}'


@dataclass(frozen=True)
class Suite:
    folder: str
    build: SuiteBuilder


# One entry per suite module under suites/. Add a suite by creating its module
# there and registering it here with the folder its tests should live in.
SUITES: list[Suite] = [
    Suite(folder="T1", build=t1_core_happy_paths.build),
]


def _ensure_folder(client: ElevenLabs, name: str) -> str:
    """Return the id of the root folder named `name`, creating it if absent."""
    cursor: str | None = None
    while True:
        page = client.conversational_ai.tests.list(types="folder", cursor=cursor)
        for entry in page.tests:
            if entry.name == name:
                return str(entry.id)
        if not page.has_more:
            break
        cursor = page.next_cursor
    return str(client.conversational_ai.tests.folders.create(name=name).id)


def _ensure_save_tool_mock(client: ElevenLabs, save_tool_id: str) -> None:
    """Make the save_call_result tool return a canned success under simulation mocking.

    Re-submits the tool's current config with response_mocks set. response_mocks is a
    top-level field on the standalone tool, not part of the agent-side inline tool schema,
    so it must be set through the tools API rather than sync_agent.
    """
    current = client.conversational_ai.tools.get(tool_id=save_tool_id)
    if getattr(current, "response_mocks", None):
        return
    request = ToolRequestModel.model_validate(
        {
            "tool_config": current.tool_config.model_dump(),
            "response_mocks": [{"mock_result": SAVE_TOOL_MOCK_RESULT, "parameter_conditions": []}],
        }
    )
    client.conversational_ai.tools.update(tool_id=save_tool_id, request=request)
    print(f"Set response mock on save_call_result tool ({save_tool_id})")


def _sync(settings: Settings) -> None:
    client = build_client(settings)
    _ensure_save_tool_mock(client, settings.save_tool_id)

    def find_existing_id(name: str, folder_id: str) -> str | None:
        cursor: str | None = None
        while True:
            page = client.conversational_ai.tests.list(
                search=name, parent_folder_id=folder_id, cursor=cursor
            )
            for test in page.tests:
                if test.name == name:
                    return str(test.id)
            if not page.has_more:
                return None
            cursor = page.next_cursor

    test_ids: list[str] = []
    for suite in SUITES:
        folder_id = _ensure_folder(client, suite.folder)
        for body in suite.build(settings.save_tool_id):
            placed = body.model_copy(update={"parent_folder_id": folder_id})
            existing_id = find_existing_id(placed.name, folder_id)
            if existing_id:
                client.conversational_ai.tests.update(test_id=existing_id, request=placed)
                test_ids.append(existing_id)
                print(f"Updated: {placed.name} ({existing_id}) [{suite.folder}]")
            else:
                created = client.conversational_ai.tests.create(request=placed)
                test_ids.append(str(created.id))
                print(f"Created: {placed.name} ({created.id}) [{suite.folder}]")

    sync_agent(client, settings, attached_test_ids=test_ids)
    print(f"Attached {len(test_ids)} test(s) to agent {settings.agent_id}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create/update ElevenLabs agent tests for an environment."
    )
    parser.add_argument("--env", required=True, help="Environment to target (e.g. dev, prod).")
    args = parser.parse_args()
    _sync(load_settings(args.env))


if __name__ == "__main__":
    main()
