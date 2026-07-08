"""Run ALL ElevenLabs agent tests against Daisy and report pass/fail.

Discovers every test in the account via tests.list(), runs them against the
environment's agent in one invocation, polls until each finishes, then prints
the verdict and the evaluator's rationale.

Never creates anything — see create_tests.py for that — so it is safe to run as
often as you like.

Run with:  uv run python apps/elevenlabs-agent/tests/agent/run_tests.py --env dev
"""

import argparse
import time

from elevenlabs.types import SingleTestRunRequestModel
from elevenlabs_agent.client import build_client
from elevenlabs_agent.config import Settings, load_settings

POLL_SECONDS = 3


def _run(settings: Settings) -> None:
    client = build_client(settings)

    test_ids: list[str] = []
    cursor: str | None = None
    while True:
        page = client.conversational_ai.tests.list(cursor=cursor)
        test_ids.extend(test.id for test in page.tests)
        if not page.has_more:
            break
        cursor = page.next_cursor

    if not test_ids:
        print("No tests found. Run create_tests.py first.")
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
    args = parser.parse_args()
    _run(load_settings(args.env))


if __name__ == "__main__":
    main()
