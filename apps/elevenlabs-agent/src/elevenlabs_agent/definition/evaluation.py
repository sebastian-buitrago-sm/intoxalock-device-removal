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
                name="Appointment slot confirmed",
                conversation_goal_prompt=(
                    "Return success ONLY if Daisy verbally confirmed a specific date "
                    "and time and the shop agreed, AND save_call_result was called "
                    "with a non-empty confirmed_slot. "
                    "Return failure if the call ended with no slot confirmed and no "
                    "shop alternatives collected. "
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
