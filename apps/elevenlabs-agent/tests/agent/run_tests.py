"""Run ElevenLabs agent tests against Daisy and report pass/fail.

Discovers tests in the account via tests.list(), runs them against the
environment's agent in one invocation, polls until each finishes, then prints
the verdict and the evaluator's rationale. The SDK mechanics live in runner.py;
this module is just the CLI and the high-level flow.

By default it runs every test. Narrow with any combination of (AND-ed):
  --folder T1_core_happy_paths   suite folder (server-side; run a whole suite)
  --type tool        test type: tool | tool-call | simulation | llm (native)
  --id test_...      exact test id (repeatable)
  --name <substr>    case-insensitive substring of the test name
  --repeat N         run each test N times (2-20; default 1 = single run) for a pass rate

    # all tests
    uv run python apps/elevenlabs-agent/tests/agent/run_tests.py --env dev
    # a whole suite
    uv run python .../run_tests.py --env dev --folder T1_core_happy_paths
    # every tool-call test
    uv run python .../run_tests.py --env dev --type tool
    # one test by id
    uv run python .../run_tests.py --env dev --id test_9801kx1vrgdse3q8ysw9m3zf94hy
    # a suite, each test 3 times, with pass-rate buckets
    uv run python .../run_tests.py --env dev --folder T1_core_happy_paths --repeat 3

With --repeat the platform runs each test repeat_count times and groups the
outcomes into buckets (server-side), so the report shows a per-test pass rate
and the distinct failure reasons — the same view as the dashboard.

The selected tests are printed before running, so selection can be verified even
if execution errors (e.g. on account quota).

Never creates anything — see sync_tests.py for that — so it is safe to run as
often as you like.
"""

import argparse

from elevenlabs_agent.client import build_client
from elevenlabs_agent.config import Settings, load_settings
from runner import (
    MAX_REPEAT,
    TYPE_ALIASES,
    TestFilters,
    announce,
    await_invocation,
    discover_tests,
    report,
    resolve_folder_id,
    select_tests,
    start_invocation,
)


def _run(settings: Settings, *, filters: TestFilters, repeat: int) -> None:
    client = build_client(settings)

    folder_id: str | None = None
    if filters.folder:
        folder_id = resolve_folder_id(client, filters.folder)
        if folder_id is None:
            print(f"No folder named {filters.folder!r}.")
            return

    tests = discover_tests(client, folder_id=folder_id, test_type=filters.test_type)
    selected = select_tests(tests, ids=filters.ids, name=filters.name)
    if not selected:
        print("No tests matched the given filters. Run sync_tests.py first if empty.")
        return

    announce(selected, repeat=repeat, agent_id=settings.agent_id)
    invocation_id = start_invocation(
        client,
        agent_id=settings.agent_id,
        test_ids=[test_id for test_id, _ in selected],
        repeat=repeat,
    )
    inv = await_invocation(client, invocation_id=invocation_id, repeat=repeat)
    report(inv, repeat=repeat)


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
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help=f"Run each selected test this many times (1-{MAX_REPEAT}) for a pass rate.",
    )
    args = parser.parse_args()
    if not 1 <= args.repeat <= MAX_REPEAT:
        parser.error(f"--repeat must be between 1 and {MAX_REPEAT}")
    filters = TestFilters(
        ids=args.ids, name=args.name, folder=args.folder, test_type=args.test_type
    )
    _run(load_settings(args.env), filters=filters, repeat=args.repeat)


if __name__ == "__main__":
    main()
