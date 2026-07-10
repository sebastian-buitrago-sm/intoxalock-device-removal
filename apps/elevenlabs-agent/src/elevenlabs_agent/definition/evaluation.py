from elevenlabs.types import EvaluationSettingsInput, PromptEvaluationCriteria


# Success evaluation criteria — run automatically on every real conversation
# (post-call analysis), distinct from the authored tests in testing/scenarios.py.
# Each `id` is stable: re-syncing updates the criterion in place rather than
# creating a duplicate. The conversation_goal_prompt spells out the failure case
# and what should fall to `unknown`, per ElevenLabs' guidance on ambiguous results.
def build_evaluation() -> EvaluationSettingsInput:
    return EvaluationSettingsInput(
        criteria=[
            PromptEvaluationCriteria(
                id="slot_confirmed",
                name="Appointment slot confirmed or alternatives collected",
                conversation_goal_prompt=(
                    "Return success if EITHER (a) Daisy verbally confirmed a specific "
                    "date and time that the shop accepted from the customer's slots, "
                    "AND save_call_result was called with a non-empty confirmed_slot; "
                    "OR (b) the shop rejected the customer's slots and Daisy captured "
                    "the shop's own availability into shop_suggested_slot_1/2 (in which "
                    "case confirmed_slot is correctly empty). "
                    "Return failure if the call ended with neither a confirmed slot nor "
                    "any shop alternatives collected. "
                    "If the transcript is cut off or the outcome cannot be "
                    "determined, this resolves to unknown."
                ),
                scope="conversation",
            ),
            PromptEvaluationCriteria(
                id="quote_requested",
                name="Device removal quote requested",
                conversation_goal_prompt=(
                    "Return success if Daisy asked the shop for a device removal quote "
                    "for the customer's vehicle (Step 4), regardless of whether the "
                    "shop gave an amount, declined, or couldn't quote by phone. Also "
                    "return success if the call ended early because the shop could "
                    "not proceed (wrong person, unavailable, asked to call back) and "
                    "save_call_result was called with no_data_reason populated — the "
                    "prompt's guardrails correctly skip the quote step in that case. "
                    "Return failure if the call reached closing (Step 5) without "
                    "Daisy ever asking for a quote and without a valid reason to skip "
                    "it. "
                    "If the transcript is cut off or the outcome cannot be "
                    "determined, this resolves to unknown."
                ),
                scope="conversation",
            ),
            PromptEvaluationCriteria(
                id="result_saved",
                name="save_call_result called before closing",
                conversation_goal_prompt=(
                    "Return success if Daisy called the save_call_result tool before "
                    "ending the call, regardless of the outcome (confirmed slot, shop "
                    "alternatives, unavailable, or technical issue). "
                    "Return failure if the call ended without that tool being called."
                ),
                scope="conversation",
            ),
        ]
    )
