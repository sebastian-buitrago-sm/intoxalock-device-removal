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
            "Saves the outcome of this scheduling call to the Mindr system. "
            "Call this tool before closing every call, without exception — whether a slot was confirmed, "
            "the shop proposed alternatives, the shop was unavailable, or a technical issue occurred. "
            "Pass all three fields every time: use an empty string for any field that does not apply."
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
                required=["confirmed_slot", "shop_suggested_slot_1", "shop_suggested_slot_2"],
                properties={
                    "confirmed_slot": LiteralJsonSchemaProperty(
                        type="string",
                        description=(
                            "The appointment slot both parties verbally agreed on. "
                            "Include the full date and time exactly as confirmed "
                            "(e.g. 'Monday June 30th at 5am'). "
                            "Pass an empty string if no slot was confirmed."
                        ),
                    ),
                    "shop_suggested_slot_1": LiteralJsonSchemaProperty(
                        type="string",
                        description=(
                            "The first available slot the shop proposed when all customer-provided slots were rejected. "
                            "Include the full date and time as stated by the shop "
                            "(e.g. 'Wednesday July 2nd at 9am'). "
                            "Pass an empty string if the shop did not suggest an alternative."
                        ),
                    ),
                    "shop_suggested_slot_2": LiteralJsonSchemaProperty(
                        type="string",
                        description=(
                            "A second backup slot proposed by the shop. "
                            "Include the full date and time as stated by the shop. "
                            "Pass an empty string if no second alternative was offered."
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
