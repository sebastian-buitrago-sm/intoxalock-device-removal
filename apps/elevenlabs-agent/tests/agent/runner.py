"""Mechanics behind run_tests.py: discover, select, announce, launch, poll, report.

Split out so run_tests.py reads as just the CLI plus the high-level flow. These
functions own the ElevenLabs SDK interaction and the two report formats — flat
for a single run, bucketed when --repeat groups the outcomes server-side.
"""

import time
from dataclasses import dataclass
from typing import cast

from elevenlabs.client import ElevenLabs
from elevenlabs.types import GetTestSuiteInvocationResponseModel, SingleTestRunRequestModel

POLL_SECONDS = 3

# ElevenLabs caps repeat_count at 20; 1 means a single, unbucketed run.
MAX_REPEAT = 20

TYPE_ALIASES = {"tool": "tool", "tool-call": "tool", "simulation": "simulation", "llm": "llm"}


@dataclass(frozen=True)
class TestFilters:
    """Which tests to run — all criteria AND-ed. folder/test_type narrow the
    server-side listing; ids/name filter that list client-side."""

    ids: list[str] | None
    name: str | None
    folder: str | None
    test_type: str | None


def is_repeating(repeat: int) -> bool:
    """A repeat count above one makes the platform run each test repeatedly and
    bucket the outcomes server-side; a count of one is a single, unbucketed run."""
    return repeat > 1


def resolve_folder_id(client: ElevenLabs, name: str) -> str | None:
    cursor: str | None = None
    while True:
        page = client.conversational_ai.tests.list(types="folder", cursor=cursor)
        for entry in page.tests:
            if entry.name == name:
                return str(entry.id)
        if not page.has_more:
            return None
        cursor = page.next_cursor


def discover_tests(
    client: ElevenLabs, *, folder_id: str | None, test_type: str | None
) -> list[tuple[str, str, str]]:
    """List every test in the account as (id, name, type), paginating. Optionally
    scoped server-side to a folder and/or a single test type."""
    list_kwargs: dict[str, object] = {}
    if folder_id:
        list_kwargs["parent_folder_id"] = folder_id
    if test_type:
        list_kwargs["types"] = TYPE_ALIASES[test_type]

    tests: list[tuple[str, str, str]] = []
    cursor: str | None = None
    while True:
        page = client.conversational_ai.tests.list(cursor=cursor, **list_kwargs)
        tests.extend((test.id, test.name, str(test.type)) for test in page.tests)
        if not page.has_more:
            return tests
        cursor = page.next_cursor


def select_tests(
    tests: list[tuple[str, str, str]], *, ids: list[str] | None, name: str | None
) -> list[tuple[str, str]]:
    """Narrow discovered tests to the (id, name) pairs matching the id set and/or
    the name substring. Folders are always excluded."""
    id_set = set(ids) if ids else None
    needle = name.lower() if name else None
    return [
        (test_id, test_name)
        for test_id, test_name, entry_type in tests
        if entry_type != "folder"
        and (id_set is None or test_id in id_set)
        and (needle is None or needle in test_name.lower())
    ]


def announce(selected: list[tuple[str, str]], *, repeat: int, agent_id: str) -> None:
    suffix = f", each x{repeat}" if is_repeating(repeat) else ""
    print(f"Running {len(selected)} test(s){suffix} against {agent_id}:")
    for _, test_name in selected:
        print(f"  - {test_name}")


def start_invocation(client: ElevenLabs, *, agent_id: str, test_ids: list[str], repeat: int) -> str:
    """Kick off the (asynchronous) run and return its invocation id. repeat_count
    is sent only when repeating, so a single run keeps the default response shape."""
    run_kwargs: dict[str, object] = {"repeat_count": repeat} if is_repeating(repeat) else {}
    invocation = client.conversational_ai.agents.run_tests(
        agent_id=agent_id,
        tests=[SingleTestRunRequestModel(test_id=test_id) for test_id in test_ids],
        **run_kwargs,
    )
    return str(invocation.id)


def await_invocation(
    client: ElevenLabs, *, invocation_id: str, repeat: int
) -> GetTestSuiteInvocationResponseModel:
    """Poll until every run reaches a terminal status and, when repeating, the
    server-side bucketing has settled; then return the final invocation."""
    while True:
        # elevenlabs.* is untyped per mypy config, so the SDK call resolves to Any.
        inv = cast(
            GetTestSuiteInvocationResponseModel,
            client.conversational_ai.tests.invocations.get(test_invocation_id=invocation_id),
        )
        runs_done = bool(inv.test_runs) and all(
            run.status in ("passed", "failed") for run in inv.test_runs
        )
        buckets_done = not is_repeating(repeat) or inv.bucketing_status in ("completed", "failed")
        if runs_done and buckets_done:
            return inv
        time.sleep(POLL_SECONDS)


def report(inv: GetTestSuiteInvocationResponseModel, *, repeat: int) -> None:
    if is_repeating(repeat) and inv.bucketing_status == "completed":
        _report_buckets(inv)
    else:
        _report_flat(inv)


def _report_flat(inv: GetTestSuiteInvocationResponseModel) -> None:
    runs = inv.test_runs
    passed = sum(1 for run in runs if run.status == "passed")
    print(f"\nResults: {passed}/{len(runs)} passed\n")
    for run in runs:
        print(f"[{str(run.status).upper()}] {run.test_name}")
        if run.condition_result is not None and run.condition_result.rationale:
            print(f"    {run.condition_result.rationale}")


def _report_buckets(inv: GetTestSuiteInvocationResponseModel) -> None:
    total = len(inv.test_runs)
    passed = sum(1 for run in inv.test_runs if run.status == "passed")
    print(f"\nResults: {passed}/{total} run(s) passed\n")
    for group in inv.result_groups or []:
        n = sum(len(bucket.test_run_ids) for bucket in group.buckets)
        won = sum(len(b.test_run_ids) for b in group.buckets if b.status == "passed")
        verdict = "PASS" if won == n else "FLAKY" if won else "FAIL"
        print(f"[{won}/{n} {verdict}] {group.test_name}")
        for bucket in group.buckets:
            count = len(bucket.test_run_ids)
            print(f"    {str(bucket.status).upper()} x{count}: {bucket.title}")
            if bucket.status != "passed" and bucket.reason:
                print(f"        {bucket.reason}")
