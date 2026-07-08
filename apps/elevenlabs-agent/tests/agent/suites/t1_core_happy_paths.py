"""Suite T1 — core revenue flow (happy paths). See scenarios.feature @T1-*.

Every happy path is a tool-call + simulation PAIR: the tool-call half locks the
saved payload (the contract); the simulation half proves Daisy navigates the flow
on her own (the journey).
"""

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
)

from .shared import (
    DYNAMIC_VARS,
    QUOTE,
    SLOT_1,
    VEHICLE_MAKE,
    VEHICLE_MODEL,
    VEHICLE_YEAR,
    exact,
)


def build(save_tool_id: str) -> list[TestsCreateRequestBody]:
    # scenarios.feature @T1-1 tool-call half.
    t1_1_tool = TestsCreateRequestBody_Tool(
        name="T1-1 · shop accepts slot 1 and quotes (tool-call)",
        dynamic_variables=DYNAMIC_VARS,
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
            Turn(
                role="agent",
                time_in_call_secs=16,
                message=(
                    f"For a {VEHICLE_YEAR} {VEHICLE_MAKE} {VEHICLE_MODEL}, "
                    "what would the installation cost?"
                ),
            ),
            Turn(role="user", time_in_call_secs=20, message=f"That'll be ${QUOTE}."),
            Turn(
                role="agent",
                time_in_call_secs=23,
                message=f"Just to confirm, that's ${QUOTE} for the installation — is that right?",
            ),
            Turn(role="user", time_in_call_secs=26, message="Yes, that's right."),
        ],
        tool_call_parameters=UnitTestToolCallEvaluationModelInput(
            referenced_tool=ReferencedToolCommonModel(id=save_tool_id, type="webhook"),
            parameters=[
                UnitTestToolCallParameter(path="confirmed_slot", eval=exact(SLOT_1)),
                UnitTestToolCallParameter(path="quote_amount", eval=exact(QUOTE)),
                UnitTestToolCallParameter(path="shop_suggested_slot_1", eval=exact("")),
                UnitTestToolCallParameter(path="shop_suggested_slot_2", eval=exact("")),
                UnitTestToolCallParameter(path="no_data_reason", eval=exact("")),
            ],
        ),
    )

    # scenarios.feature @T1-1 (simulation half) — proves Daisy navigates
    # offer -> accept -> confirm -> quote -> save -> close on her own. Tools are
    # mocked so save_call_result never hits the real webhook.
    t1_1_sim = TestsCreateRequestBody_Simulation(
        name="T1-1 · shop accepts slot 1 and quotes (simulation)",
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            f"You DO have availability for the first time slot she proposes. "
            "When she asks if you have an opening for that first slot, say yes, that works. "
            "When she repeats the slot back to confirm, confirm it clearly. "
            f"When she asks what the installation would cost for the vehicle, say it is ${QUOTE}. "
            "When she repeats the price back to confirm, confirm it clearly. "
            "Do NOT propose any alternative times. Keep your replies short and natural."
        ),
        tool_mock_config=SimulationToolMockBehaviorConfig(
            mocking_strategy="all",
            fallback_strategy="raise_error",
        ),
        simulation_max_turns=15,
        success_condition=(
            f"The agent confirmed the appointment for '{SLOT_1}', obtained an installation "
            f"quote of ${QUOTE}, called save_call_result before closing, and ended the call "
            "politely without misunderstandings."
        ),
    )

    return [t1_1_tool, t1_1_sim]
