from typing import cast

from elevenlabs.client import ElevenLabs
from elevenlabs.types import TwilioOutboundCallResponse

from elevenlabs_agent.config import Settings


def place_call(
    client: ElevenLabs,
    settings: Settings,
    to_number: str,
    dynamic_variables: dict[str, str],
) -> TwilioOutboundCallResponse:
    # elevenlabs.* is untyped per mypy config, so the SDK call resolves to Any
    # even though it returns TwilioOutboundCallResponse at runtime.
    return cast(
        TwilioOutboundCallResponse,
        client.conversational_ai.twilio.outbound_call(
            agent_id=settings.agent_id,
            agent_phone_number_id=settings.phone_number_id,
            to_number=to_number,
            conversation_initiation_client_data={"dynamic_variables": dynamic_variables},
        ),
    )
