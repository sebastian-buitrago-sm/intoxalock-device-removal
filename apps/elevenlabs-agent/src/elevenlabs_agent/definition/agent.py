from dataclasses import dataclass
from typing import Any

from elevenlabs.types import (
    AgentCallLimits,
    AgentConfig,
    AgentPlatformSettingsRequestModel,
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

VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
TTS_MODEL_ID = "eleven_flash_v2"
LLM = "gpt-5-mini"
BACKUP_LLM_ORDER = ["gpt-5-mini", "claude-sonnet-4"]
TIMEZONE = "America/New_York"

DYNAMIC_VARIABLE_PLACEHOLDERS: dict[str, str | float | int | bool | list[Any] | None] = {
    "user_id": "unique identifier for the customer record used to route the call result to the correct account",
    "user_scheduled_slot_1": "preferred date and time for the customer's Ignition Interlock Device removal appointment",
    "user_scheduled_slot_2": "alternative date and time for the customer's Ignition Interlock Device removal appointment",
}


@dataclass(frozen=True)
class AgentDefinition:
    conversation_config: ConversationalConfig
    platform_settings: AgentPlatformSettingsRequestModel


def build_agent_definition(settings: Settings) -> AgentDefinition:
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
                timezone=TIMEZONE,
                tools=build_tools(settings.webhook_base_url),
                backup_llm_config=PromptAgentApiModelOutputBackupLlmConfig_Override(
                    order=BACKUP_LLM_ORDER,
                ),
            ),
        ),
    )
    platform_settings = AgentPlatformSettingsRequestModel(
        evaluation=build_evaluation(),
        call_limits=AgentCallLimits(
            agent_concurrency_limit=settings.concurrency_limit,
            bursting_enabled=False,
        ),
    )
    return AgentDefinition(
        conversation_config=conversation_config,
        platform_settings=platform_settings,
    )
