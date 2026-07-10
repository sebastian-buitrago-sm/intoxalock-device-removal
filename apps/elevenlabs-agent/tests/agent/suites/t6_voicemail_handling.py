"""Suite T6 — voicemail handling. See scenarios.feature @T6-*.

Graduated out of @needs-spec (was NS-1) once prompt.py defined a policy: leave
a brief, generic message and save with no_data_reason = "reached voicemail",
skipping scheduling and the quote entirely.

The voicemail_detection system tool's result is scriptable
(ConversationHistoryTranscriptSystemToolResultCommonModelInputResult_VoicemailDetectionSuccess),
so its firing is seeded into chat_history deterministically — the same
tool_call/tool_result shape T4 uses for a failed save_call_result attempt —
rather than run as a full simulation: the model can't organically "become" an
answering machine, and the assertion is about exact saved parameters, not
multi-turn navigation.
"""

from elevenlabs.conversational_ai.tests.types import (
    TestsCreateRequestBody,
    TestsCreateRequestBody_Tool,
)
from elevenlabs.types import (
    ConversationHistoryTranscriptCommonModelInput,
    ConversationHistoryTranscriptSystemToolResultCommonModelInput,
    ConversationHistoryTranscriptSystemToolResultCommonModelInputResult_VoicemailDetectionSuccess,
    ConversationHistoryTranscriptToolCallCommonModelInput,
    ReferencedToolCommonModel,
    UnitTestToolCallEvaluationModelInput,
    UnitTestToolCallParameter,
    UnitTestToolCallParameterEval_Llm,
)
from elevenlabs_agent.definition.prompt import FIRST_MESSAGE

from .shared import DYNAMIC_VARS, body_path, exact, slug_name, turn

_VOICEMAIL_TOOL_NAME = "voicemail_detection"
_REQUEST_ID = "t6-1-voicemail"


def _voicemail_detected_turns(at_sec: int) -> list[ConversationHistoryTranscriptCommonModelInput]:
    """Seed one already-fired voicemail_detection result as 2 granular turns
    (tool_call, then tool_result) — mirrors T4's failed save_call_result shape,
    since a live transcript always represents a tool call/result as distinct
    turns, never merged onto one with a spoken line."""
    return [
        ConversationHistoryTranscriptCommonModelInput(
            role="agent",
            time_in_call_secs=at_sec,
            tool_calls=[
                ConversationHistoryTranscriptToolCallCommonModelInput(
                    type="system",
                    request_id=_REQUEST_ID,
                    tool_name=_VOICEMAIL_TOOL_NAME,
                    params_as_json="{}",
                    tool_has_been_called=True,
                )
            ],
        ),
        ConversationHistoryTranscriptCommonModelInput(
            role="agent",
            time_in_call_secs=at_sec,
            tool_results=[
                ConversationHistoryTranscriptSystemToolResultCommonModelInput(
                    request_id=_REQUEST_ID,
                    tool_name=_VOICEMAIL_TOOL_NAME,
                    result_value='{"status": "success"}',
                    is_error=False,
                    tool_has_been_called=True,
                    result=ConversationHistoryTranscriptSystemToolResultCommonModelInputResult_VoicemailDetectionSuccess(
                        status="success"
                    ),
                )
            ],
        ),
    ]


def build(save_tool_id: str) -> list[TestsCreateRequestBody]:
    # scenarios.feature @T6-1 — seeded history shows voicemail_detection already
    # fired (tool_call + success result, no spoken line of its own). Asserts the
    # model's next save_call_result call carries no scheduling/quote data and a
    # voicemail reason.
    t6_1_tool = TestsCreateRequestBody_Tool(
        name=slug_name("t6_1__tool_call", "call is answered by voicemail"),
        dynamic_variables=DYNAMIC_VARS,
        chat_history=[
            turn("agent", FIRST_MESSAGE, 0),
            *_voicemail_detected_turns(2),
        ],
        tool_call_parameters=UnitTestToolCallEvaluationModelInput(
            referenced_tool=ReferencedToolCommonModel(
                id=save_tool_id, type="api_integration_webhook"
            ),
            parameters=[
                UnitTestToolCallParameter(path=body_path("confirmed_slot"), eval=exact("")),
                UnitTestToolCallParameter(path=body_path("shop_suggested_slot_1"), eval=exact("")),
                UnitTestToolCallParameter(path=body_path("shop_suggested_slot_2"), eval=exact("")),
                UnitTestToolCallParameter(path=body_path("quote_amount"), eval=exact("")),
                UnitTestToolCallParameter(
                    path=body_path("no_data_reason"),
                    eval=UnitTestToolCallParameterEval_Llm(
                        description=(
                            "Indicates the call reached voicemail or an answering machine as "
                            "the reason no scheduling or quote data was gathered."
                        )
                    ),
                ),
            ],
        ),
    )

    return [t6_1_tool]
