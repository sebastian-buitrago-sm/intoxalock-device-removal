"""Create (or update) the ElevenLabs agent tests for Daisy.

These are the agent's *conversational* tests (simulation + tool-call), run on
the ElevenLabs platform against the deployed agent — distinct from the pytest
suite one level up, which covers this project's own Python code.

Idempotent: each test is looked up by name and updated if it exists, otherwise
created — so re-running never produces duplicates. Which agent (and which
save_call_result tool id) it targets is chosen by --env.

Run with:  uv run python apps/elevenlabs-agent/tests/agent/create_tests.py --env dev
"""

import argparse

from elevenlabs.conversational_ai.tests.types import (
    TestsCreateRequestBody,
    TestsCreateRequestBody_Simulation,
    TestsCreateRequestBody_Tool,
)
from elevenlabs.types import (
    ConversationHistoryTranscriptCommonModelInput as Turn,
)
from elevenlabs.types import (
    ReferencedToolCommonModel,
    SimulationToolMockBehaviorConfig,
    UnitTestToolCallEvaluationModelInput,
    UnitTestToolCallParameter,
    UnitTestToolCallParameterEval_Exact,
)
from elevenlabs_agent.client import build_client
from elevenlabs_agent.config import Settings, load_settings

# Concrete values so the prompt's {{placeholders}} resolve during the test.
SLOT_1 = "Monday June 30th at 5am"
SLOT_2 = "Tuesday July 1st at 9am"


def _exact(value: str) -> UnitTestToolCallParameterEval_Exact:
    return UnitTestToolCallParameterEval_Exact(expected_value=value)


def build_tests(save_tool_id: str) -> list[TestsCreateRequestBody]:
    # Scenario 1 (tool call): shop accepts slot 1 -> save_call_result invoked with
    # that slot. We supply the conversation up to the point Daisy should save and
    # assert the tool arguments. Tool-call parameter verification belongs to this
    # test type; simulation tests only judge the conversation outcome.
    scenario_1 = TestsCreateRequestBody_Tool(
        name="Scenario 1 - shop accepts slot 1, saved as confirmed_slot",
        dynamic_variables={
            "user_id": "test-user-001",
            "user_scheduled_slot_1": SLOT_1,
            "user_scheduled_slot_2": SLOT_2,
        },
        chat_history=[
            Turn(
                role="agent",
                time_in_call_secs=0,
                message=(
                    "Hi, I am Daisy calling from Intoxalock. We have a customer requesting "
                    "an installation appointment. May I check your availability?"
                ),
            ),
            Turn(role="user", time_in_call_secs=4, message="Sure, go ahead."),
            Turn(role="agent", time_in_call_secs=6, message=f"Do you have an opening on {SLOT_1}?"),
            Turn(role="user", time_in_call_secs=9, message="Yes, that time works for us."),
            Turn(
                role="agent",
                time_in_call_secs=11,
                message=f"Let me confirm: {SLOT_1} — is that correct?",
            ),
            Turn(role="user", time_in_call_secs=14, message="Yes, that's correct."),
        ],
        tool_call_parameters=UnitTestToolCallEvaluationModelInput(
            referenced_tool=ReferencedToolCommonModel(id=save_tool_id, type="webhook"),
            parameters=[
                UnitTestToolCallParameter(path="confirmed_slot", eval=_exact(SLOT_1)),
                UnitTestToolCallParameter(path="shop_suggested_slot_1", eval=_exact("")),
                UnitTestToolCallParameter(path="shop_suggested_slot_2", eval=_exact("")),
            ],
        ),
    )

    # Scenario 1 (simulation): a simulated "shop" plays out the full call and an
    # evaluation model judges the OUTCOME. Complements the tool test above: the tool
    # test verifies the saved payload (the contract); this verifies the agent
    # navigates offer -> accept -> confirm on its own (the journey). Tools are mocked
    # so save_call_result never hits the real webhook during the test.
    scenario_1_sim = TestsCreateRequestBody_Simulation(
        name="Scenario 1 (sim) - shop accepts slot 1, conversation reaches confirmation",
        dynamic_variables={
            "user_id": "test-user-001",
            "user_scheduled_slot_1": SLOT_1,
            "user_scheduled_slot_2": SLOT_2,
        },
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            f"You DO have availability for the first time slot she proposes ({SLOT_1}). "
            "When she asks if you have an opening for that first slot, say yes, that works. "
            "When she repeats the slot back to confirm, confirm it clearly. "
            "Do NOT propose any alternative times. Keep your replies short and natural."
        ),
        tool_mock_config=SimulationToolMockBehaviorConfig(
            mocking_strategy="all",
            fallback_strategy="raise_error",
        ),
        simulation_max_turns=15,
        success_condition=(
            f"The agent confirmed the appointment for '{SLOT_1}', completed the call "
            "without misunderstandings, and ended politely."
        ),
    )

    return [scenario_1, scenario_1_sim]


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

    for test in build_tests(settings.save_tool_id):
        existing_id = find_existing_id(test.name)
        if existing_id:
            client.conversational_ai.tests.update(test_id=existing_id, request=test)
            print(f"Updated: {test.name} ({existing_id})")
        else:
            created = client.conversational_ai.tests.create(request=test)
            print(f"Created: {test.name} ({created.id})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create/update ElevenLabs agent tests for an environment."
    )
    parser.add_argument("--env", required=True, help="Environment to target (e.g. dev, prod).")
    args = parser.parse_args()
    _sync(load_settings(args.env))


if __name__ == "__main__":
    main()
