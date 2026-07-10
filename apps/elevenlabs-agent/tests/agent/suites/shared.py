"""Shared fixtures for the test suites: concrete dynamic-variable values + helpers.

Concrete values so the prompt's {{placeholders}} resolve during a test. Step 4
quotes the vehicle, so every test supplies the vehicle placeholders too — not just
the slots — or the {{...}} render empty and the quote turn reads unnaturally.
"""

import re
from typing import Any, Literal

from elevenlabs.types import (
    ConversationHistoryTranscriptCommonModelInput,
    UnitTestToolCallParameterEval_Exact,
    UnitTestToolCallParameterEval_Regex,
)

# today_shop_local anchors the year so natural-language slots resolve to a specific
# ISO date. June 30 2025 is a Monday and July 1 2025 a Tuesday, matching the weekday
# words in SLOT_1/SLOT_2; the shop alternates fall on the following days.
TODAY_SHOP_LOCAL = "Sunday, June 29, 2025"

SLOT_1 = "Monday June 30th at 5am"
SLOT_2 = "Tuesday July 1st at 9am"
SLOT_1_ISO = "2025-06-30 05:00"
SLOT_2_ISO = "2025-07-01 09:00"

SHOP_ALT_1 = "Wednesday July 2nd at 9am"
SHOP_ALT_2 = "Thursday July 3rd at 2pm"
SHOP_ALT_1_ISO = "2025-07-02 09:00"
SHOP_ALT_2_ISO = "2025-07-03 14:00"

VEHICLE_YEAR = "2019"
VEHICLE_MAKE = "Honda"
VEHICLE_MODEL = "Civic"
QUOTE = "250"

DYNAMIC_VARS: dict[str, str | float | int | bool | list[Any] | None] = {
    "user_id": "test-user-001",
    "user_scheduled_slot_1": SLOT_1,
    "user_scheduled_slot_2": SLOT_2,
    "user_vehicle_year": VEHICLE_YEAR,
    "user_vehicle_make": VEHICLE_MAKE,
    "user_vehicle_model": VEHICLE_MODEL,
    "today_shop_local": TODAY_SHOP_LOCAL,
}


def exact(value: str) -> UnitTestToolCallParameterEval_Exact:
    return UnitTestToolCallParameterEval_Exact(expected_value=value)


def iso_slot(value: str) -> UnitTestToolCallParameterEval_Regex:
    """Match an ISO 'YYYY-MM-DD HH:MM' slot, tolerating a missing hour leading zero
    or a trailing ':00' seconds the model may emit — the date and time still pin exactly."""
    date, time = value.split(" ")
    hour, minute = time.split(":")
    pattern = rf"^{re.escape(date)}[ T]0?{int(hour)}:{re.escape(minute)}(:00)?$"
    return UnitTestToolCallParameterEval_Regex(pattern=pattern)


def body_path(field: str) -> str:
    """Address a webhook request-body field in a tool-call parameter assertion.

    ElevenLabs resolves a tool-call `path` against the structured call
    (body / path_params / query_params), so body fields must be prefixed
    "body." — a bare field name evaluates as "not found in tool call parameters".
    """
    return f"body.{field}"


def path_param_path(field: str) -> str:
    """Address a webhook path parameter (e.g. user_id) — see body_path."""
    return f"path_params.{field}"


def turn(
    role: Literal["user", "agent"], message: str, at_sec: int
) -> ConversationHistoryTranscriptCommonModelInput:
    """Build one seeded chat_history turn for a partial-sim test.

    role "agent" is Daisy; role "user" is the shop (ElevenLabs' generic name for
    the other party on the call, regardless of call direction).
    """
    return ConversationHistoryTranscriptCommonModelInput(
        role=role, message=message, time_in_call_secs=at_sec
    )


def slug_name(slug: str, description: str) -> str:
    """Compose a test name from a stable snake_case slug and a human description.

    The slug (e.g. "t1_1__tool_call") is the identity handle sync_tests keys on and
    the leading token filters like --name match; the description keeps the dashboard
    label legible.
    """
    return f"{slug} · {description}"
