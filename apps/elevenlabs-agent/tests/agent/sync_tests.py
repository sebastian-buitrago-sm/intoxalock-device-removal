"""Create (or update) the ElevenLabs agent tests for Daisy.

These are the agent's *conversational* tests (simulation + tool-call), run on
the ElevenLabs platform against the deployed agent — distinct from the pytest
suite one level up, which covers this project's own Python code.

Tests are organized into suites under suites/, one module per suite, mirroring
scenarios.feature (T1..T4 tiers, E edge cases, NS needs-spec). Each suite module
exposes build(save_tool_id) -> list[TestsCreateRequestBody]; register a new suite
by adding its module to SUITES below.

Idempotent: each test is looked up by name and updated if it exists, otherwise
created — so re-running never produces duplicates. Which agent (and which
save_call_result tool id) it targets is chosen by --env.

After syncing, the tests are attached to the env's agent (via sync_agent) so
they surface under the agent's Tests tab and run against it. Because a plain
`agent sync-agent` sends no test ids and clears the attachments, run this AFTER
sync-agent, not before.

Run with:  uv run python apps/elevenlabs-agent/tests/agent/sync_tests.py --env dev
"""

import argparse
from collections.abc import Callable

from elevenlabs.conversational_ai.tests.types import TestsCreateRequestBody
from elevenlabs_agent.client import build_client
from elevenlabs_agent.config import Settings, load_settings
from elevenlabs_agent.sync.agent_sync import sync_agent
from suites import t1_core_happy_paths

SuiteBuilder = Callable[[str], list[TestsCreateRequestBody]]

# One entry per suite module under suites/. Add a suite by creating its module
# there and registering its build function here.
SUITES: list[SuiteBuilder] = [
    t1_core_happy_paths.build,
]


def build_tests(save_tool_id: str) -> list[TestsCreateRequestBody]:
    tests: list[TestsCreateRequestBody] = []
    for build in SUITES:
        tests.extend(build(save_tool_id))
    return tests


def _sync(settings: Settings) -> None:
    client = build_client(settings)

    def find_existing_id(name: str) -> str | None:
        cursor: str | None = None
        while True:
            page = client.conversational_ai.tests.list(search=name, cursor=cursor)
            for test in page.tests:
                if test.name == name:
                    return str(test.id)
            if not page.has_more:
                return None
            cursor = page.next_cursor

    test_ids: list[str] = []
    for test in build_tests(settings.save_tool_id):
        existing_id = find_existing_id(test.name)
        if existing_id:
            client.conversational_ai.tests.update(test_id=existing_id, request=test)
            test_ids.append(existing_id)
            print(f"Updated: {test.name} ({existing_id})")
        else:
            created = client.conversational_ai.tests.create(request=test)
            test_ids.append(str(created.id))
            print(f"Created: {test.name} ({created.id})")

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
