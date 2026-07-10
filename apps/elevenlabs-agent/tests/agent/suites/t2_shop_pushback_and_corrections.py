"""Suite T2 — shop pushback & corrections. See scenarios.feature @T2-*.

Every scenario is a full-simulation TestsCreateRequestBody_Simulation, run from
scratch rather than seeded with a chat_history prefix: scripting Daisy's own
early turns would assume she reaches the branch under test instead of proving
it, which is exactly what @simulation is meant to guarantee. Some of these
share their lead-in with a T1 happy-path twin (noted per scenario below) —
that's accepted overlap cost in exchange for proving the deeper, more specific
behavior is reached autonomously, not seeded in.
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
)


def build(save_tool_id: str) -> list[TestsCreateRequestBody]:
    mock_config = SimulationToolMockBehaviorConfig(
        mocking_strategy="selected",
        mocked_tool_ids=[save_tool_id],
        fallback_strategy="call_real_tool",
    )

    # scenarios.feature @T2-2 — shares its reject-slot-1/accept-slot-2 lead-in with
    # T1-2 (already proven there), but run from scratch so the reversal-and-reconfirm
    # behavior is reached by Daisy's own navigation rather than assumed via seeded
    # history; proves she re-confirms rather than saving the slot she just repeated
    # back once the shop reverses to the other known slot.
    t2_2_sim = TestsCreateRequestBody_Simulation(
        name=slug_name("t2_2__simulation", "shop reverses to the other slot after Daisy confirms"),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule a device removal appointment. "
            "You do NOT have availability for the FIRST time slot she proposes — say you are "
            "fully booked that day. You DO have availability for the SECOND time slot she "
            "proposes — say yes, that works. "
            f"When she repeats the second slot ({SLOT_2}) back to confirm it, say you misspoke — "
            f"you actually meant {SLOT_1}, not {SLOT_2}. "
            "When she repeats the corrected slot back, confirm it clearly. "
            f"When she asks what the device removal would cost, say it is ${QUOTE}. When she "
            "repeats the price back to confirm, confirm it clearly. Keep replies short."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=18,
        success_condition=(
            f"The agent was told slot '{SLOT_1}' was unavailable, moved to slot '{SLOT_2}' and "
            f"began confirming it, then re-confirmed '{SLOT_1}' after the shop reversed away "
            f"from '{SLOT_2}', obtained a device removal quote, called save_call_result with "
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
            "Daisy is calling to schedule a device removal appointment. "
            "You DO have availability for the first time slot she proposes. When she asks "
            "if you have an opening for that first slot, say yes, that works. When she "
            "repeats the slot back to confirm, confirm it clearly. "
            "When she asks what the device removal would cost, say you can't give a price over "
            "the phone and the customer will need to ask in person. Do NOT give any number. "
            "Keep your replies short and natural."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=15,
        success_condition=(
            f"The agent confirmed the appointment for '{SLOT_1}', asked for a quote, accepted "
            "the shop's decline gracefully without pressing for a number, called "
            "save_call_result with quote_amount empty and no_data_reason populated describing why "
            "no quote was obtained before closing, then called end_call to end the call politely."
        ),
    )

    # scenarios.feature @T2-4 — the callback request fires before any slot is offered,
    # the same "shop can't proceed" guardrail path as T1-4/T2-5.
    t2_4_sim = TestsCreateRequestBody_Simulation(
        name=slug_name("t2_4__simulation", "shop asks Daisy to call back later"),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule a device removal appointment. "
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
            "Daisy is calling to schedule a device removal appointment. "
            "Before she can propose a time, say your shop cannot take any device removal "
            "appointments right now, full stop. Do NOT discuss any time slot or price. Keep "
            "your reply short and natural."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=10,
        success_condition=(
            "The agent was told the shop cannot take any device removal appointments, did NOT "
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
            "Daisy is calling to schedule a device removal appointment. "
            "For the first THREE questions she asks you (about any slot, availability, or "
            'price), respond non-committally — "maybe", "let me check and get back to '
            'you", or similar — instead of a clear yes/no or number. From the FOURTH question '
            "onward, answer normally and cooperatively: accept a slot, confirm it, and give a "
            f"price of ${QUOTE} when asked. Keep replies short."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=20,
        success_condition=(
            "The agent kept asking one clarifying question at a time without giving up when "
            "met with non-committal answers, eventually reached a confirmed slot and a "
            "device removal quote, called save_call_result before closing, then called end_call "
            "to end the call politely, all within the allotted turns."
        ),
    )

    # scenarios.feature @T2-7 — shares its reject-both/offer-two-alternatives lead-in
    # with T1-3 (already proven there), but run from scratch so the correction-after-
    # readback behavior is reached by Daisy's own navigation rather than assumed via
    # seeded history; proves she re-reads BOTH alternatives with the correction
    # applied, the same correction-after-readback risk as T2-2 but for the
    # two-alternative branch.
    t2_7_sim = TestsCreateRequestBody_Simulation(
        name=slug_name(
            "t2_7__simulation", "shop corrects one of two alternatives after Daisy reads them back"
        ),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule a device removal appointment. "
            "You do NOT have availability for EITHER of the two time slots she proposes — say "
            "you're fully booked both times. "
            f"When she asks for your next available date and time, offer {SHOP_ALT_1}. "
            f"When she asks for a second available time, offer {SHOP_ALT_2}. "
            f"When she reads both back to make sure she has them right, correct her on the first "
            f"one only — say the actual time for that day is an hour later than what she said. "
            f"Confirm the second time ({SHOP_ALT_2}) is correct as stated. When she reads both "
            "back again with the correction, confirm they are correct now. "
            f"When she asks what the device removal would cost, say it is ${QUOTE}. When she "
            "repeats the price back to confirm, confirm it clearly. Stay on the line after that — "
            "do NOT end the call yourself; let Daisy close it. Keep replies short."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=22,
        success_condition=(
            "The agent was told both customer slots were unavailable, captured two "
            "shop-proposed alternatives, read them back for accuracy, then re-read BOTH "
            "alternatives back with the correction applied to the first one (not just "
            "acknowledged it in passing) before moving on, obtained a device removal quote, "
            "called save_call_result with confirmed_slot empty and both shop_suggested_slot_1/2 "
            "reflecting the corrected values before closing, then called end_call to end the "
            "call politely."
        ),
    )

    # scenarios.feature @T2-8 — distinct from T2-2 (reverses to the OTHER customer slot,
    # still a valid confirmed_slot) and T2-7 (corrects an already-shop-suggested
    # alternative). Here the shop retracts its own acceptance of a customer slot and
    # substitutes a date that is neither customer slot — proves Daisy does NOT save that
    # substitution as confirmed_slot, and instead falls through to the Step 2 alternatives
    # branch (asking for a second available time) rather than treating a single
    # shop-volunteered date as good enough.
    t2_8_sim = TestsCreateRequestBody_Simulation(
        name=slug_name(
            "t2_8__simulation",
            "shop retracts an accepted slot and substitutes a date matching neither customer slot",
        ),
        dynamic_variables=DYNAMIC_VARS,
        simulation_scenario=(
            "You are an employee at a vehicle service center who just answered the phone. "
            "Daisy is calling to schedule a device removal appointment. "
            "You do NOT have availability for the FIRST time slot she proposes — say you are "
            "fully booked that day. You DO say yes to the SECOND time slot she proposes. "
            f"When she repeats that second slot back to confirm it, say you actually don't have "
            f"that either — you misread the schedule — and instead offer {SHOP_ALT_1}, a "
            "completely different date from either of the two she originally asked about. "
            f"When she asks for a second available time, offer {SHOP_ALT_2}. When she reads both "
            "back to make sure she has them right, confirm they are correct. "
            f"When she asks what the device removal would cost, say it is ${QUOTE}. When she "
            "repeats the price back to confirm, confirm it clearly. Stay on the line after that — "
            "do NOT end the call yourself; let Daisy close it. Keep replies short."
        ),
        tool_mock_config=mock_config,
        simulation_max_turns=20,
        success_condition=(
            f"The agent was told slot '{SLOT_1}' was unavailable, was initially told slot "
            f"'{SLOT_2}' worked, but when repeating '{SLOT_2}' back to confirm, the shop retracted "
            f"and substituted '{SHOP_ALT_1}' — a date matching NEITHER customer slot. The agent "
            "did NOT save that substituted date as confirmed_slot; instead it treated it as a "
            "shop-suggested alternative, asked for a SECOND available time, and read both back "
            "for accuracy (not as a confirmation) before obtaining a device removal quote. "
            "Called save_call_result with confirmed_slot EMPTY and shop_suggested_slot_1/2 "
            "reflecting the shop's own two dates before closing, then called end_call to end the "
            "call politely."
        ),
    )

    return [t2_2_sim, t2_3_sim, t2_4_sim, t2_5_sim, t2_6_sim, t2_7_sim, t2_8_sim]
