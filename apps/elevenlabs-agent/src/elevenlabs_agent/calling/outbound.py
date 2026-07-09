from datetime import datetime
from typing import cast
from zoneinfo import ZoneInfo

from elevenlabs.client import ElevenLabs
from elevenlabs.types import TwilioOutboundCallResponse

from elevenlabs_agent.config import Settings


def resolve_today_local(timezone: str) -> str:
    today = datetime.now(ZoneInfo(timezone))
    return f"{today:%A, %B} {today.day}, {today:%Y}"


def place_call(
    client: ElevenLabs,
    settings: Settings,
    *,
    to_number: str,
    shop_timezone: str,
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
            conversation_initiation_client_data={
                "dynamic_variables": {
                    **dynamic_variables,
                    "today_shop_local": resolve_today_local(shop_timezone),
                }
            },
        ),
    )
