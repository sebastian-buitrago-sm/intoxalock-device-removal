from elevenlabs.client import ElevenLabs

from elevenlabs_agent.config import Settings


def build_client(settings: Settings) -> ElevenLabs:
    return ElevenLabs(api_key=settings.api_key)
