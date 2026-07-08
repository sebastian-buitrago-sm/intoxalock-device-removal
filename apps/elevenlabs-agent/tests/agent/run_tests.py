"""Run ElevenLabs agent tests against Daisy and report pass/fail.

Discovers tests in the account via tests.list(), runs them against the
environment's agent in one invocation, polls until each finishes, then prints
the verdict and the evaluator's rationale.

By default it runs every test. Narrow with any combination of (AND-ed):
  --folder T1        suite folder (server-side; run a whole suite)
  --type tool        test type: tool | tool-call | simulation | llm (native)
  --id test_...      exact test id (repeatable)
  --name <substr>    case-insensitive substring of the test name

    # all tests
    uv run python apps/elevenlabs-agent/tests/agent/run_tests.py --env dev
    # a whole suite
    uv run python .../run_tests.py --env dev --folder T1
    # every tool-call test
    uv run python .../run_tests.py --env dev --type tool
    # one test by id
    uv run python .../run_tests.py --env dev --id test_9801kx1vrgdse3q8ysw9m3zf94hy

The selected tests are printed before running, so selection can be verified even
if execution errors (e.g. on account quota).

Never creates anything — see sync_tests.py for that — so it is safe to run as
often as you like.
"""

import argparse
import time

from elevenlabs.client import ElevenLabs
from elevenlabs.types import SingleTestRunRequestModel
from elevenlabs_agent.client import build_client
from elevenlabs_agent.config import Settings, load_settings

POLL_SECONDS = 3

TYPE_ALIASES = {"tool": "tool", "tool-call": "tool", "simulation": "simulation", "llm": "llm"}


def _resolve_folder_id(client: ElevenLabs, name: str) -> str | None:
    cursor: str | None = None
    while True:
        page = client.conversational_ai.tests.list(types="folder", cursor=cursor)
        for entry in page.tests:
            if entry.name == name:
                return str(entry.id)
        if not page.has_more:
            return None
        cursor = page.next_cursor


def _run(
    settings: Settings,
    ids: list[str] | None,
    name: str | None,
    folder: str | None,
    test_type: str | None,
) -> None:
    client = build_client(settings)

    list_kwargs: dict[str, object] = {}
    if folder:
        folder_id = _resolve_folder_id(client, folder)
        if folder_id is None:
            print(f"No folder named {folder!r}.")
            return
        list_kwargs["parent_folder_id"] = folder_id
    if test_type:
        list_kwargs["types"] = TYPE_ALIASES[test_type]

    tests: list[tuple[str, str, str]] = []
    cursor: str | None = None
    while True:
        page = client.conversational_ai.tests.list(cursor=cursor, **list_kwargs)
        tests.extend((test.id, test.name, str(test.type)) for test in page.tests)
        if not page.has_more:
            break
        cursor = page.next_cursor

    id_set = set(ids) if ids else None
    needle = name.lower() if name else None
    selected = [
        (test_id, test_name)
        for test_id, test_name, entry_type in tests
        if entry_type != "folder"
        and (id_set is None or test_id in id_set)
        and (needle is None or needle in test_name.lower())
    ]

    if not selected:
        print("No tests matched the given filters. Run sync_tests.py first if empty.")
        return

    print(f"Running {len(selected)} test(s) against {settings.agent_id}:")
    for _, test_name in selected:
        print(f"  - {test_name}")

    invocation = client.conversational_ai.agents.run_tests(
        agent_id=settings.agent_id,
        tests=[SingleTestRunRequestModel(test_id=test_id) for test_id, _ in selected],
    )

    while True:
        inv = client.conversational_ai.tests.invocations.get(test_invocation_id=invocation.id)
        if all(run.status in ("passed", "failed") for run in inv.test_runs):
            break
        time.sleep(POLL_SECONDS)

    passed = sum(1 for run in inv.test_runs if run.status == "passed")
    print(f"\nResults: {passed}/{len(inv.test_runs)} passed\n")
    for run in inv.test_runs:
        print(f"[{str(run.status).upper()}] {run.test_name}")
        if run.condition_result is not None and run.condition_result.rationale:
            print(f"    {run.condition_result.rationale}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ElevenLabs agent tests against an environment."
    )
    parser.add_argument("--env", required=True, help="Environment to target (e.g. dev, prod).")
    parser.add_argument(
        "--id",
        dest="ids",
        action="append",
        help="Only run the test with this exact id. Repeatable.",
    )
    parser.add_argument(
        "--name",
        help="Only run tests whose name contains this (case-insensitive).",
    )
    parser.add_argument(
        "--folder",
        help="Only run tests in this suite folder (e.g. T1).",
    )
    parser.add_argument(
        "--type",
        dest="test_type",
        choices=sorted(TYPE_ALIASES),
        help="Only run tests of this type.",
    )
    args = parser.parse_args()
    _run(load_settings(args.env), args.ids, args.name, args.folder, args.test_type)


if __name__ == "__main__":
    main()
