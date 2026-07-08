"""Run ElevenLabs agent tests against Daisy and report pass/fail.

Discovers tests in the account via tests.list(), runs them against the
environment's agent in one invocation, polls until each finishes, then prints
the verdict and the evaluator's rationale.

By default it runs every test. Narrow to specific ones with --id (exact test
id, repeatable) and/or --name (case-insensitive substring of the test name):

    # all tests
    uv run python apps/elevenlabs-agent/tests/agent/run_tests.py --env dev
    # one test by id
    uv run python .../run_tests.py --env dev --id test_9801kx1vrgdse3q8ysw9m3zf94hy
    # every test whose name contains "tool-call"
    uv run python .../run_tests.py --env dev --name tool-call

Never creates anything — see sync_tests.py for that — so it is safe to run as
often as you like.
"""

import argparse
import time

from elevenlabs.types import SingleTestRunRequestModel
from elevenlabs_agent.client import build_client
from elevenlabs_agent.config import Settings, load_settings

POLL_SECONDS = 3


def _run(settings: Settings, ids: list[str] | None, name: str | None) -> None:
    client = build_client(settings)

    tests: list[tuple[str, str]] = []
    cursor: str | None = None
    while True:
        page = client.conversational_ai.tests.list(cursor=cursor)
        tests.extend((test.id, test.name) for test in page.tests)
        if not page.has_more:
            break
        cursor = page.next_cursor

    if not tests:
        print("No tests found. Run sync_tests.py first.")
        return

    id_set = set(ids) if ids else None
    needle = name.lower() if name else None
    test_ids = [
        test_id
        for test_id, test_name in tests
        if (id_set is None or test_id in id_set) and (needle is None or needle in test_name.lower())
    ]

    if not test_ids:
        print("No tests matched the given --id/--name filters.")
        return

    print(f"Running {len(test_ids)} test(s) against {settings.agent_id}...")
    invocation = client.conversational_ai.agents.run_tests(
        agent_id=settings.agent_id,
        tests=[SingleTestRunRequestModel(test_id=tid) for tid in test_ids],
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
    args = parser.parse_args()
    _run(load_settings(args.env), args.ids, args.name)


if __name__ == "__main__":
    main()
