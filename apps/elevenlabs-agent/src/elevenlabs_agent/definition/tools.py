from elevenlabs.types import (
    LiteralJsonSchemaProperty,
    ObjectJsonSchemaPropertyOutput,
    PromptAgentApiModelOutputToolsItem,
    PromptAgentApiModelOutputToolsItem_System,
    PromptAgentApiModelOutputToolsItem_Webhook,
    WebhookToolApiSchemaConfigOutput,
)
from elevenlabs.types.system_tool_config_output_params import (
    SystemToolConfigOutputParams_EndCall,
    SystemToolConfigOutputParams_VoicemailDetection,
)

SAVE_CALL_RESULT_TOOL_NAME = "save_call_result"


def _voicemail_detection_tool() -> PromptAgentApiModelOutputToolsItem_System:
    return PromptAgentApiModelOutputToolsItem_System(
        name="voicemail_detection",
        description="",
        params=SystemToolConfigOutputParams_VoicemailDetection(),
    )


def _end_call_tool() -> PromptAgentApiModelOutputToolsItem_System:
    return PromptAgentApiModelOutputToolsItem_System(
        name="end_call",
        description="",
        params=SystemToolConfigOutputParams_EndCall(),
    )


def _save_call_result_tool(webhook_base_url: str) -> PromptAgentApiModelOutputToolsItem_Webhook:
    return PromptAgentApiModelOutputToolsItem_Webhook(
        name=SAVE_CALL_RESULT_TOOL_NAME,
        description=(
            "Saves the outcome of this scheduling call to the Intoxalock system. "
            "Call this tool before closing every call, without exception — whether a slot was confirmed, "
            "the shop proposed alternatives, the shop was unavailable, or a technical issue occurred. "
            "Pass all five fields every time: use an empty string for any field that does not apply. "
            "confirmed_slot is populated ONLY when the shop accepted one of the customer's slots; when "
            "the shop instead proposed its own times, leave confirmed_slot empty and put those times in "
            "shop_suggested_slot_1/2. All slot values use ISO 24-hour format 'YYYY-MM-DD HH:MM'."
        ),
        api_schema=WebhookToolApiSchemaConfigOutput(
            url=f"{webhook_base_url}/save-call-result/{{{{user_id}}}}",
            method="POST",
            path_params_schema={
                "user_id": LiteralJsonSchemaProperty(
                    type="string",
                    description="Unique identifier for the customer record, injected at call initiation.",
                )
            },
            request_body_schema=ObjectJsonSchemaPropertyOutput(
                type="object",
                required=[
                    "confirmed_slot",
                    "shop_suggested_slot_1",
                    "shop_suggested_slot_2",
                    "quote_amount",
                    "no_data_reason",
                ],
                properties={
                    "confirmed_slot": LiteralJsonSchemaProperty(
                        type="string",
                        description=(
                            "The customer-provided slot the shop accepted and Daisy verbally confirmed. "
                            "ISO 24-hour format 'YYYY-MM-DD HH:MM', resolved to a specific calendar date "
                            "(e.g. '2026-06-30 05:00'). "
                            "Pass an empty string if the shop accepted no customer slot — including when "
                            "it offered its own alternative times instead (those go in shop_suggested_slot_1/2)."
                        ),
                    ),
                    "shop_suggested_slot_1": LiteralJsonSchemaProperty(
                        type="string",
                        description=(
                            "The first time the shop proposed after rejecting all customer-provided slots. "
                            "ISO 24-hour format 'YYYY-MM-DD HH:MM', resolved to a specific calendar date "
                            "(e.g. '2026-07-02 09:00'). "
                            "Pass an empty string if the shop did not suggest an alternative."
                        ),
                    ),
                    "shop_suggested_slot_2": LiteralJsonSchemaProperty(
                        type="string",
                        description=(
                            "A second time the shop proposed as a backup. "
                            "ISO 24-hour format 'YYYY-MM-DD HH:MM', resolved to a specific calendar date. "
                            "Pass an empty string if no second alternative was offered."
                        ),
                    ),
                    "quote_amount": LiteralJsonSchemaProperty(
                        type="string",
                        description=(
                            "The installation quote the shop gave for the customer's vehicle, in whole "
                            "USD, digits only (e.g. '250'). No currency symbol or words. "
                            "Pass an empty string if the shop did not provide a quote."
                        ),
                    ),
                    "no_data_reason": LiteralJsonSchemaProperty(
                        type="string",
                        description=(
                            "Short reason no scheduling data could be gathered on this call "
                            "(e.g. 'shop unavailable at the moment', 'person in charge not available', "
                            "'shop asked to call back'). "
                            "Pass an empty string if the call proceeded normally, regardless of outcome."
                        ),
                    ),
                },
            ),
        ),
    )


def build_tools(webhook_base_url: str) -> list[PromptAgentApiModelOutputToolsItem]:
    return [
        _voicemail_detection_tool(),
        _end_call_tool(),
        _save_call_result_tool(webhook_base_url),
    ]
