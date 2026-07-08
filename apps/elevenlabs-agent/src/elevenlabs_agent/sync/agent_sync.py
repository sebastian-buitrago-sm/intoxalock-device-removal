from collections.abc import Sequence
from typing import cast

from elevenlabs.client import ElevenLabs
from elevenlabs.types import CreateAgentResponseModel, GetAgentResponseModel

from elevenlabs_agent.config import Settings
from elevenlabs_agent.definition import build_agent_definition


def create_agent(client: ElevenLabs, settings: Settings) -> CreateAgentResponseModel:
    """Create a brand-new agent from the definition (from-scratch workflow).

    Does not touch settings.agent_id — there is none yet. Just returns the new
    agent's id; nothing is written to config/<env>.toml automatically.
    """
    definition = build_agent_definition(settings)
    return cast(
        CreateAgentResponseModel,
        client.conversational_ai.agents.create(
            name=settings.agent_name,
            tags=settings.tags,
            conversation_config=definition.conversation_config,
            platform_settings=definition.platform_settings,
        ),
    )


def sync_agent(
    client: ElevenLabs,
    settings: Settings,
    attached_test_ids: Sequence[str] | None = None,
) -> GetAgentResponseModel:
    """Push the agent definition to the environment's target agent, in place.

    Idempotent: updates the existing agent identified by settings.agent_id
    rather than creating a new one, so re-running never produces duplicates.

    When attached_test_ids is given, those tests are attached to the agent so
    they surface under the agent's Tests tab and run against it. They are
    resent as the full platform_settings, so evaluation and call limits are
    preserved rather than wiped.
    """
    definition = build_agent_definition(settings, attached_test_ids)
    # elevenlabs.* is untyped per mypy config, so the SDK call resolves to Any
    # even though it returns GetAgentResponseModel at runtime.
    return cast(
        GetAgentResponseModel,
        client.conversational_ai.agents.update(
            agent_id=settings.agent_id,
            name=settings.agent_name,
            tags=settings.tags,
            conversation_config=definition.conversation_config,
            platform_settings=definition.platform_settings,
        ),
    )
