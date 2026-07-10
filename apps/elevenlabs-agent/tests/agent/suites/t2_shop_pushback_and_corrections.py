"""Suite T2 — shop pushback & corrections. See scenarios.feature @T2-*.

Every scenario is a TestsCreateRequestBody_Simulation — full simulations for
scenarios that start from scratch, and the same type seeded with a chat_history
prefix ("partial-sim" in scenarios.feature) for scenarios whose risk lives deep
in the flow, so re-simulating the turns before it is unnecessary cost/variance.
No tool-call tests: where a scenario completes the workflow, its
success_condition checks the quote + save_call_result + end_call together.
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
    turn,
)


def build(save_tool_id: str) -> list[TestsCreateRequestBody]:
    mock_config = SimulationToolMockBehaviorConfig(
        mocking_strategy="selected",
        mocked_tool_ids=[save_tool_id],
        fallback_strategy="call_real_tool",
    )

    # scenarios.feature @T2-1 — seeded past both rejections so only the
    # one-alternative-offer branch is simulated; proves Daisy does not fabricate a
    # second alternative when the shop genuinely has only one.
    t2_1_sim = TestsCreateRequestBody_Simulation(
        name=slug_name(
            "t2_1__simulation", "shop rejects both slots and offers only one alternative"
        ),
        dynamic_variables=DYNAMIC_VARS,
        chat_history=[
            turn("agent", f"Do you have an opening on {SLOT_1}?", 0),
            turn("user", "No, sorry, we're fully booked that day.", 4),
            turn("agent", f"No problem. Do you have an opening on {SLOT_2}?", 8),
            turn("user", "No, we don't have that time either.", 12),
            turn(
                "agent",
                "No problem. Can you share your next available date and time for an "
                "installation?",
                16,
            ),
        ],
        simulation_scenario=(
            "You are an employee at a vehicle service center, mid-call with Daisy. She has "
            "just asked for your next available date and time, since neither of the "
            "customer's proposed times worked. "
            f"Offer {SHOP_ALT_1}. "
            "When she asks for a SECOND available time, say that's the only opening you have "
            "right now — do NOT offer a second time. "
            "When she reads the time back to make sure she has it right, confirm it is "
            "correct — this is an accuracy check, not a booking confirmation. "
            f"When she asks what the installation would cost, say it is ${QUOTE}. When she "
            "repeats the price back to confirm, confirm it clearly. Keep replies short."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=12,
        success_condition=(
            f"The agent read the single shop-proposed alternative ('{SHOP_ALT_1}') back as an "
            "accuracy check (not a booking confirmation) and did NOT fabricate or ask a third "
            "time for a second alternative after being told there wasn't one, obtained an "
            "installation quote, called save_call_result before closing, then called end_call "
            "to end the call politely."
        ),
    )

    # scenarios.feature @T2-2 — seeded to the confirmation step with slot 2 already
    # accepted; proves Daisy re-confirms rather than saving the slot she just repeated
    # back once the shop reverses to the other known slot.
    t2_2_sim = TestsCreateRequestBody_Simulation(
        name=slug_name(
            "t2_2__simulation", "shop reverses to the other slot after Daisy confirms"
        ),
        dynamic_variables=DYNAMIC_VARS,
        chat_history=[
            turn("agent", f"Do you have an opening on {SLOT_1}?", 0),
            turn("user", "No, sorry, we're fully booked that day.", 4),
            turn("agent", f"No problem. Do you have an opening on {SLOT_2}?", 8),
            turn("user", "Yes, that works.", 12),
            turn("agent", f"Let me confirm: {SLOT_2} — is that correct?", 16),
        ],
        simulation_scenario=(
            "You are an employee at a vehicle service center, mid-call with Daisy. She has "
            f"just repeated {SLOT_2} back to confirm it. "
            f"Say you misspoke — you actually meant {SLOT_1}, not {SLOT_2}. "
            "When she repeats the corrected slot back, confirm it clearly. "
            f"When she asks what the installation would cost, say it is ${QUOTE}. When she "
            "repeats the price back to confirm, confirm it clearly. Keep replies short."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=10,
        success_condition=(
            f"The agent re-confirmed '{SLOT_1}' after the shop reversed away from "
            f"'{SLOT_2}', obtained an installation quote, called save_call_result with "
            f"confirmed_slot = {SLOT_1} (not {SLOT_2}) before closing, then called end_call "
            "to end the call politely without misunderstandings."
        ),
    )

    # scenarios.feature @T2-3 — the risk is purely behavioral (accept the decline
    # gracefully, without pressing), so this runs as a full simulation from scratch.
    t2_3_sim = TestsCreateRequestBody_Simulation(
        name=slug_name("t2_3__simulation", "shop declines or cannot give a quote by phone"),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            "You DO have availability for the first time slot she proposes. When she asks "
            "if you have an opening for that first slot, say yes, that works. When she "
            "repeats the slot back to confirm, confirm it clearly. "
            "When she asks what the installation would cost, say you can't give a price over "
            "the phone and the customer will need to ask in person. Do NOT give any number. "
            "Keep your replies short and natural."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=15,
        success_condition=(
            f"The agent confirmed the appointment for '{SLOT_1}', asked for a quote, accepted "
            "the shop's decline gracefully without pressing for a number, called "
            "save_call_result with quote_amount empty before closing, then called end_call to "
            "end the call politely."
        ),
    )

    # scenarios.feature @T2-4 — the callback request fires before any slot is offered,
    # the same "shop can't proceed" guardrail path as T1-4/T2-5.
    t2_4_sim = TestsCreateRequestBody_Simulation(
        name=slug_name("t2_4__simulation", "shop asks Daisy to call back later"),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            "Before she can propose a time, ask her to call back later — say you're busy "
            "right now and can't talk. Do NOT discuss any time slot or price. Keep your reply "
            "short and natural."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=10,
        success_condition=(
            "The agent was asked to call back later, acknowledged politely, did NOT attempt "
            "the quote step, called save_call_result with all four slot/quote fields empty "
            "and no_data_reason describing the callback request, then called end_call to end "
            "the call politely."
        ),
    )

    # scenarios.feature @T2-5 — no appointment capacity at all fires before any slot is
    # offered, the same "shop can't proceed" guardrail path as T1-4/T2-4.
    t2_5_sim = TestsCreateRequestBody_Simulation(
        name=slug_name("t2_5__simulation", "shop has no appointment capacity at all"),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            "Before she can propose a time, say your shop cannot take any installation "
            "appointments right now, full stop. Do NOT discuss any time slot or price. Keep "
            "your reply short and natural."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=10,
        success_condition=(
            "The agent was told the shop cannot take any installation appointments, did NOT "
            "attempt the quote step, called save_call_result with no_data_reason populated and "
            "all four slot/quote fields empty, then called end_call to end the call politely."
        ),
    )

    # scenarios.feature @T2-6 — non-committal stalling is inherently multi-turn emergent
    # behavior; run this one with --repeat and gate on a pass-rate (flakiest in the suite).
    t2_6_sim = TestsCreateRequestBody_Simulation(
        name=slug_name("t2_6__simulation", "shop gives non-committal answers repeatedly"),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule an installation appointment. "
            "For the first THREE questions she asks you (about any slot, availability, or "
            "price), respond non-committally — \"maybe\", \"let me check and get back to "
            "you\", or similar — instead of a clear yes/no or number. From the FOURTH question "
            "onward, answer normally and cooperatively: accept a slot, confirm it, and give a "
            f"price of ${QUOTE} when asked. Keep replies short."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=20,
        success_condition=(
            "The agent kept asking one clarifying question at a time without giving up when "
            "met with non-committal answers, eventually reached a confirmed slot and an "
            "installation quote, called save_call_result before closing, then called end_call "
            "to end the call politely, all within the allotted turns."
        ),
    )

    # scenarios.feature @T2-7 — seeded past the reject-both-and-offer-two-alternatives
    # branch to the accuracy read-back; proves Daisy re-reads BOTH alternatives with the
    # correction applied, the same correction-after-readback risk as T2-2 but for the
    # two-alternative branch (T1-3/T1-5).
    t2_7_sim = TestsCreateRequestBody_Simulation(
        name=slug_name(
            "t2_7__simulation", "shop corrects one of two alternatives after Daisy reads them back"
        ),
        dynamic_variables=DYNAMIC_VARS,
        chat_history=[
            turn("agent", f"Do you have an opening on {SLOT_1}?", 0),
            turn("user", "No, sorry, we're fully booked that day.", 4),
            turn("agent", f"No problem. Do you have an opening on {SLOT_2}?", 8),
            turn("user", "No, we don't have that time either.", 12),
            turn(
                "agent",
                "No problem. Can you share your next available date and time for an "
                "installation?",
                16,
            ),
            turn("user", f"Sure, {SHOP_ALT_1} works.", 20),
            turn(
                "agent",
                "Can I know a second available time, in case the first doesn't work for our "
                "customer?",
                24,
            ),
            turn("user", f"Yes, {SHOP_ALT_2} as well.", 28),
            turn(
                "agent",
                f"Let me make sure I have these right: {SHOP_ALT_1}, and {SHOP_ALT_2} — is "
                "that correct?",
                32,
            ),
        ],
        simulation_scenario=(
            "You are an employee at a vehicle service center, mid-call with Daisy. She has "
            f"just read back {SHOP_ALT_1} and {SHOP_ALT_2} to make sure she has them right. "
            f"Correct her on the first one only — say the actual time for that day is an hour "
            f"later than what she said. Confirm the second time ({SHOP_ALT_2}) is correct as "
            "stated. When she reads both back again with the correction, confirm they are "
            "correct now. "
            f"When she asks what the installation would cost, say it is ${QUOTE}. When she "
            "repeats the price back to confirm, confirm it clearly. Keep replies short."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=12,
        success_condition=(
            "The agent re-read BOTH alternatives back with the correction applied to the first "
            "one (not just acknowledged it in passing) before moving on, obtained an "
            "installation quote, called save_call_result with confirmed_slot empty and both "
            "shop_suggested_slot_1/2 reflecting the corrected values before closing, then "
            "called end_call to end the call politely."
        ),
    )

    return [t2_1_sim, t2_2_sim, t2_3_sim, t2_4_sim, t2_5_sim, t2_6_sim, t2_7_sim]
