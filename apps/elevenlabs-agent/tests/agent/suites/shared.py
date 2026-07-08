"""Shared fixtures for the test suites: concrete dynamic-variable values + helpers.

Concrete values so the prompt's {{placeholders}} resolve during a test. Step 4
quotes the vehicle, so every test supplies the vehicle placeholders too — not just
the slots — or the {{...}} render empty and the quote turn reads unnaturally.
"""

from typing import Any

from elevenlabs.types import UnitTestToolCallParameterEval_Exact

SLOT_1 = "Monday June 30th at 5am"
SLOT_2 = "Tuesday July 1st at 9am"
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
}


def exact(value: str) -> UnitTestToolCallParameterEval_Exact:
    return UnitTestToolCallParameterEval_Exact(expected_value=value)
