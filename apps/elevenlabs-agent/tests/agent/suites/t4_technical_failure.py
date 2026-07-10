"""Suite T4 — technical / failure. See scenarios.feature @T4-*.

Both scenarios pin prompt.py's save_call_result retry contract (retry once on
failure; apologize and end gracefully if it fails twice). Both run as
TestsCreateRequestBody_Tool: chat_history is scripted through one or two already-
failed save_call_result attempts, and tool_call_parameters asserts the model's
very next tool call. No live tool mocking involved.

A failed attempt is baked into chat_history as three separate agent-role turns —
a message, then a tool_calls-only turn, then a tool_results-only turn — mirroring
exactly how a live transcript represents it (confirmed by inspecting one: message,
tool_call, and tool_result are always distinct turns, never merged onto one). An
earlier version of this suite merged all three onto a single turn; the platform
silently discarded that turn and regenerated fresh from the last real user turn
instead of treating it as history to continue from, which is why it's split here.

T4-2 needs no live mock at all: end_call's spoken line and reason are parameters
of the end_call tool call itself (see a live transcript's params_as_json —
system__message_to_speak / reason are flat keys, not a preceding message turn),
so the apologize-and-close behavior is asserted the same way as T4-1's retry —
via tool_call_parameters on the model's next tool call after two seeded failures.
"""

import json

from elevenlabs.conversational_ai.tests.types import (
    TestsCreateRequestBody,
    TestsCreateRequestBody_Tool,
)
from elevenlabs.types import (
    ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelInput,
    ConversationHistoryTranscriptCommonModelInput,
    ConversationHistoryTranscriptToolCallCommonModelInput,
    ReferencedToolCommonModel,
    UnitTestToolCallEvaluationModelInput,
    UnitTestToolCallParameter,
    UnitTestToolCallParameterEval_Llm,
)
from elevenlabs_agent.definition.prompt import FIRST_MESSAGE
from elevenlabs_agent.definition.tools import SAVE_CALL_RESULT_TOOL_NAME

from .shared import (
    DYNAMIC_VARS,
    QUOTE,
    SLOT_1,
    SLOT_1_ISO,
    VEHICLE_MAKE,
    VEHICLE_MODEL,
    VEHICLE_YEAR,
    body_path,
    exact,
    iso_slot,
    slug_name,
    turn,
)

_SAVE_CALL_RESULT_PARAMS = {
    "confirmed_slot": SLOT_1_ISO,
    "shop_suggested_slot_1": "",
    "shop_suggested_slot_2": "",
    "quote_amount": QUOTE,
    "no_data_reason": "",
}
_ERROR_RESULT_VALUE = '{"error": "rate limited", "status": 429}'


def _tool_call_turn(
    tool_name: str, request_id: str, params: dict[str, str], at_sec: int
) -> ConversationHistoryTranscriptCommonModelInput:
    return ConversationHistoryTranscriptCommonModelInput(
        role="agent",
        time_in_call_secs=at_sec,
        tool_calls=[
            ConversationHistoryTranscriptToolCallCommonModelInput(
                type="api_integration_webhook",
                request_id=request_id,
                tool_name=tool_name,
                params_as_json=json.dumps(params),
                tool_has_been_called=True,
            )
        ],
    )


def _tool_result_turn(
    tool_name: str, request_id: str, at_sec: int
) -> ConversationHistoryTranscriptCommonModelInput:
    return ConversationHistoryTranscriptCommonModelInput(
        role="agent",
        time_in_call_secs=at_sec,
        tool_results=[
            ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelInput(
                request_id=request_id,
                tool_name=tool_name,
                result_value=_ERROR_RESULT_VALUE,
                is_error=True,
                tool_has_been_called=True,
                type="api_integration_webhook",
            )
        ],
    )


def _failed_save_call_result_attempt(
    request_id: str, at_sec: int
) -> list[ConversationHistoryTranscriptCommonModelInput]:
    """Seed one already-failed save_call_result attempt as 2 granular turns
    (tool_call, then tool_result) — no spoken line of its own. A pre-spoken
    "technical issue" line reads to the model as "the retry already happened",
    so which failure this is has to be inferred from the attempt count alone.
    """
    return [
        _tool_call_turn(SAVE_CALL_RESULT_TOOL_NAME, request_id, _SAVE_CALL_RESULT_PARAMS, at_sec),
        _tool_result_turn(SAVE_CALL_RESULT_TOOL_NAME, request_id, at_sec),
    ]


_LEAD_IN = [
    turn("agent", FIRST_MESSAGE, 0),
    turn("user", "Yes, that works for us.", 5),
    turn(
        "agent",
        f"Great, you're all set for {SLOT_1}. And what would the device removal "
        f"cost for a {VEHICLE_YEAR} {VEHICLE_MAKE} {VEHICLE_MODEL}?",
        10,
    ),
    turn("user", f"That'll be ${QUOTE}.", 15),
]


def build(save_tool_id: str) -> list[TestsCreateRequestBody]:
    # scenarios.feature @T4-1 — the seeded history already shows one failed
    # save_call_result attempt (tool_call + is_error result, no spoken line of its
    # own — a pre-spoken "technical issue" line reads to the model as "the retry
    # already happened", so the failure count has to speak for itself) so the test
    # asserts the model's very next tool call is a retry carrying the identical
    # confirmed data, not a fresh (possibly different) payload.
    t4_1_tool = TestsCreateRequestBody_Tool(
        name=slug_name("t4_1__tool_call", "save_call_result fails once, retry succeeds"),
        dynamic_variables=DYNAMIC_VARS,
        chat_history=[
            *_LEAD_IN,
            *_failed_save_call_result_attempt("t4-1-attempt-1", 20),
        ],
        tool_call_parameters=UnitTestToolCallEvaluationModelInput(
            referenced_tool=ReferencedToolCommonModel(
                id=save_tool_id, type="api_integration_webhook"
            ),
            parameters=[
                UnitTestToolCallParameter(
                    path=body_path("confirmed_slot"), eval=iso_slot(SLOT_1_ISO)
                ),
                UnitTestToolCallParameter(path=body_path("shop_suggested_slot_1"), eval=exact("")),
                UnitTestToolCallParameter(path=body_path("shop_suggested_slot_2"), eval=exact("")),
                UnitTestToolCallParameter(path=body_path("quote_amount"), eval=exact(QUOTE)),
                UnitTestToolCallParameter(path=body_path("no_data_reason"), eval=exact("")),
            ],
        ),
    )

    # scenarios.feature @T4-2 — the seeded history shows TWO already-failed
    # save_call_result attempts, neither with a spoken line of its own (see T4-1's
    # comment on why: a pre-spoken line reads as "the retry already happened",
    # confusing which failure this is); the test asserts the model's next tool call
    # is end_call, not a third save_call_result attempt.
    #
    # Only `reason` is checked, not the spoken apology: a live run showed the
    # apology is said in its own preceding message turn ("I'm sorry, something
    # went wrong. An Intoxalock representative will be in touch with you shortly.
    # Have a great day!" — exactly prompt.py's scripted line) and end_call's own
    # system__message_to_speak param is NOT reliably populated to match it (this
    # run omitted it entirely) — tool_call_parameters can only inspect the
    # referenced tool's own params, not a preceding message turn's text, so the
    # spoken apology itself isn't asserted by this test.
    t4_2_tool = TestsCreateRequestBody_Tool(
        name=slug_name("t4_2__tool_call", "save_call_result fails twice in a row"),
        dynamic_variables=DYNAMIC_VARS,
        chat_history=[
            *_LEAD_IN,
            *_failed_save_call_result_attempt("t4-2-attempt-1", 20),
            *_failed_save_call_result_attempt("t4-2-attempt-2", 25),
        ],
        tool_call_parameters=UnitTestToolCallEvaluationModelInput(
            referenced_tool=ReferencedToolCommonModel(id="end_call", type="system"),
            parameters=[
                UnitTestToolCallParameter(
                    path="reason",
                    eval=UnitTestToolCallParameterEval_Llm(
                        description=(
                            "Indicates save_call_result failed (e.g. a technical issue, "
                            "error, or repeated failure) as the reason the call is ending."
                        )
                    ),
                ),
            ],
        ),
    )

    return [t4_1_tool, t4_2_tool]
