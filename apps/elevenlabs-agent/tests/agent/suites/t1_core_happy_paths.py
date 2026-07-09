"""Suite T1 — core revenue flow (happy paths). See scenarios.feature @T1-*.

Each happy path is a simulation that proves Daisy navigates the flow on her own
(the journey), ending in save_call_result + a clean close.
"""

from elevenlabs.conversational_ai.tests.types import (
    TestsCreateRequestBody,
    TestsCreateRequestBody_Simulation,
)
from elevenlabs.types import SimulationToolMockBehaviorConfig

from .shared import (
    DYNAMIC_VARS,
    QUOTE,
    SHOP_ALT_1,
    SHOP_ALT_2,
    SLOT_1,
    SLOT_2,
    slug_name,
)


def build(save_tool_id: str) -> list[TestsCreateRequestBody]:
    # scenarios.feature @T1-1 — proves Daisy navigates
    # offer -> accept -> confirm -> quote -> save -> close on her own. save_call_result
    # is mocked by id; other tools (notably end_call) run for real so the call can end
    # cleanly. mocking_strategy="all" leaves the webhook unmocked (platform mocks only
    # "mockable" tools), which raises "no mock matched" — hence "selected" by id.
    t1_1_sim = TestsCreateRequestBody_Simulation(
        name=slug_name("t1_1__simulation", "shop accepts slot 1 and quotes"),
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
            mocking_strategy="selected",
            mocked_tool_ids=[save_tool_id],
            fallback_strategy="call_real_tool",
        ),
        simulation_max_turns=15,
        success_condition=(
            f"The agent confirmed the appointment for '{SLOT_1}', obtained an installation "
            f"quote of ${QUOTE}, called save_call_result before closing, then called end_call "
            "to end the call politely without misunderstandings."
        ),
    )

    # scenarios.feature @T1-2 — proves Daisy navigates the
    # reject-then-offer-next branch on her own before quoting and closing.
    t1_2_sim = TestsCreateRequestBody_Simulation(
        name=slug_name("t1_2__simulation", "shop rejects slot 1, accepts slot 2, and quotes"),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            "You do NOT have availability for the FIRST time slot she proposes — say you are "
            "fully booked that day. You DO have availability for the SECOND time slot she "
            "proposes — say yes, that works. "
            "When she repeats the second slot back to confirm, confirm it clearly. "
            f"When she asks what the installation would cost for the vehicle, say it is ${QUOTE}. "
            "When she repeats the price back to confirm, confirm it clearly. "
            "Keep your replies short and natural."
        ),
        tool_mock_config=SimulationToolMockBehaviorConfig(
            mocking_strategy="selected",
            mocked_tool_ids=[save_tool_id],
            fallback_strategy="call_real_tool",
        ),
        simulation_max_turns=15,
        success_condition=(
            f"The agent was told slot '{SLOT_1}' was unavailable, confirmed the appointment for "
            f"'{SLOT_2}' instead, obtained an installation quote of ${QUOTE}, called "
            "save_call_result before closing, then called end_call to end the call politely "
            "without misunderstandings."
        ),
    )

    # scenarios.feature @T1-3 — proves Daisy navigates the
    # reject-both -> ask-shop-availability -> capture-two-alternatives branch on her own,
    # reading both back for accuracy (not a confirmation) before quoting and closing.
    t1_3_sim = TestsCreateRequestBody_Simulation(
        name=slug_name(
            "t1_3__simulation", "shop rejects both slots, offers two alternatives, and quotes"
        ),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            "You do NOT have availability for EITHER of the two time slots she proposes — say "
            "you're fully booked both times. "
            f"When she asks for your next available date and time, offer {SHOP_ALT_1}. "
            f"When she asks for a second available time, offer {SHOP_ALT_2}. "
            "When she reads both times back to make sure she has them right, confirm they are "
            "correct — this is an accuracy check, not a booking confirmation. "
            f"When she asks what the installation would cost for the vehicle, say it is ${QUOTE}. "
            "When she repeats the price back to confirm, confirm it clearly. "
            "Keep your replies short and natural."
        ),
        tool_mock_config=SimulationToolMockBehaviorConfig(
            mocking_strategy="selected",
            mocked_tool_ids=[save_tool_id],
            fallback_strategy="call_real_tool",
        ),
        simulation_max_turns=15,
        success_condition=(
            f"The agent was told both customer slots were unavailable, captured two "
            f"shop-proposed alternatives ('{SHOP_ALT_1}' and '{SHOP_ALT_2}') without treating "
            f"them as a confirmed appointment, obtained an installation quote of ${QUOTE}, "
            "called save_call_result before closing, then called end_call to end the call "
            "politely without misunderstandings."
        ),
    )

    # scenarios.feature @T1-5 — proves Daisy navigates the
    # reject-both -> single-alternative-only branch on her own before quoting and closing.
    t1_5_sim = TestsCreateRequestBody_Simulation(
        name=slug_name(
            "t1_5__simulation", "shop rejects both slots, offers one alternative, and quotes"
        ),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            "You do NOT have availability for EITHER of the two time slots she proposes — say "
            "you're fully booked both times. "
            f"When she asks for your next available date and time, offer {SHOP_ALT_1}. "
            "When she asks for a SECOND available time, say that's the only opening you have "
            "right now — do NOT offer a second time. "
            "When she reads the single time back to make sure she has it right, confirm it is "
            "correct — this is an accuracy check, not a booking confirmation. "
            f"When she asks what the installation would cost for the vehicle, say it is ${QUOTE}. "
            "When she repeats the price back to confirm, confirm it clearly. "
            "Keep your replies short and natural."
        ),
        tool_mock_config=SimulationToolMockBehaviorConfig(
            mocking_strategy="selected",
            mocked_tool_ids=[save_tool_id],
            fallback_strategy="call_real_tool",
        ),
        simulation_max_turns=15,
        success_condition=(
            f"The agent was told both customer slots were unavailable, captured a single "
            f"shop-proposed alternative ('{SHOP_ALT_1}') without treating it as a confirmed "
            f"appointment and without fabricating a second alternative, obtained an installation "
            f"quote of ${QUOTE}, called save_call_result before closing, then called end_call "
            "to end the call politely without misunderstandings."
        ),
    )

    # scenarios.feature @T1-4 — proves Daisy recognizes the
    # scheduling contact is unavailable, skips the quote step, and saves with
    # no_data_reason populated instead.
    t1_4_sim = TestsCreateRequestBody_Simulation(
        name=slug_name(
            "t1_4__simulation", "scheduling contact is not available"
        ),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            "Before she can propose a time, say that the person who handles scheduling is not "
            "in right now and you can't help with that. "
            "Do NOT offer to take a message with any time slot, and do NOT discuss a price. "
            "Keep your reply short and natural."
        ),
        tool_mock_config=SimulationToolMockBehaviorConfig(
            mocking_strategy="selected",
            mocked_tool_ids=[save_tool_id],
            fallback_strategy="call_real_tool",
        ),
        simulation_max_turns=15,
        success_condition=(
            "The agent was told the scheduling contact was not available, did NOT ask for an "
            "installation quote, called save_call_result with all four slot/quote fields empty "
            "and no_data_reason populated describing why, then called end_call to end the call "
            "politely without misunderstandings."
        ),
    )

    return [t1_1_sim, t1_2_sim, t1_3_sim, t1_4_sim, t1_5_sim]
