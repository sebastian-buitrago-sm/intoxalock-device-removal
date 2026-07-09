from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from elevenlabs.types import (
    AgentCallLimits,
    AgentConfig,
    AgentPlatformSettingsRequestModel,
    AgentTestingSettings,
    AgentWorkspaceOverridesInput,
    AttachedTestModel,
    ConvAiWebhooks,
    ConversationalConfig,
    DynamicVariablesConfigOutput,
    PromptAgentApiModelOutput,
    PromptAgentApiModelOutputBackupLlmConfig_Override,
    TtsConversationalConfigOutput,
)

from elevenlabs_agent.config import Settings
from elevenlabs_agent.definition.evaluation import build_evaluation
from elevenlabs_agent.definition.prompt import FIRST_MESSAGE, PROMPT
from elevenlabs_agent.definition.tools import build_tools

VOICE_ID = "DXFkLCBUTmvXpp2QwZjA"
TTS_MODEL_ID = "eleven_flash_v2"
LLM = "claude-haiku-4-5"
BACKUP_LLM_ORDER = ["gpt-5-mini"]

DYNAMIC_VARIABLE_PLACEHOLDERS: dict[str, str | float | int | bool | list[Any] | None] = {
    "user_id": "unique identifier for the customer record used to route the call result to the correct account",
    "user_scheduled_slot_1": "preferred date and time for the customer's Ignition Interlock Device removal appointment",
    "user_scheduled_slot_2": "alternative date and time for the customer's Ignition Interlock Device removal appointment",
    "user_vehicle_make": "make of the customer's vehicle, e.g. Honda",
    "user_vehicle_model": "model of the customer's vehicle, e.g. Civic",
    "user_vehicle_year": "model year of the customer's vehicle, e.g. 2019",
    "today_shop_local": (
        "today's date at the shop's location, e.g. 'Thursday, July 9, 2026' — reference point for "
        "resolving relative dates the shop states, such as 'tomorrow' or 'next Monday'"
    ),
}


@dataclass(frozen=True)
class AgentDefinition:
    conversation_config: ConversationalConfig
    platform_settings: AgentPlatformSettingsRequestModel


def build_agent_definition(
    settings: Settings,
    attached_test_ids: Sequence[str] | None = None,
    post_call_webhook_id: str | None = None,
) -> AgentDefinition:
    conversation_config = ConversationalConfig(
        tts=TtsConversationalConfigOutput(voice_id=VOICE_ID, model_id=TTS_MODEL_ID),
        agent=AgentConfig(
            first_message=FIRST_MESSAGE,
            dynamic_variables=DynamicVariablesConfigOutput(
                dynamic_variable_placeholders=DYNAMIC_VARIABLE_PLACEHOLDERS,
            ),
            prompt=PromptAgentApiModelOutput(
                prompt=PROMPT,
                llm=LLM,
                tools=build_tools(settings.webhook_base_url),
                backup_llm_config=PromptAgentApiModelOutputBackupLlmConfig_Override(
                    order=BACKUP_LLM_ORDER,
                ),
            ),
        ),
    )
    platform_settings_kwargs: dict[str, Any] = {
        "evaluation": build_evaluation(),
        "call_limits": AgentCallLimits(
            agent_concurrency_limit=settings.concurrency_limit,
            bursting_enabled=False,
        ),
        "testing": AgentTestingSettings(
            attached_tests=[
                AttachedTestModel(test_id=test_id) for test_id in attached_test_ids or []
            ]
        ),
    }
    if post_call_webhook_id:
        platform_settings_kwargs["workspace_overrides"] = AgentWorkspaceOverridesInput(
            webhooks=ConvAiWebhooks(
                post_call_webhook_id=post_call_webhook_id,
                events=["transcript", "call_initiation_failure"],
            )
        )
    platform_settings = AgentPlatformSettingsRequestModel(**platform_settings_kwargs)
    return AgentDefinition(
        conversation_config=conversation_config,
        platform_settings=platform_settings,
    )
