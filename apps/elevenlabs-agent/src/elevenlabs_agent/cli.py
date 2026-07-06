import os

from core.greeting import greet


def main() -> None:
    """Print the shared greeting and, if configured, probe the ElevenLabs SDK."""
    print(greet())

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("(ELEVENLABS_API_KEY not set - skipping ElevenLabs SDK probe)")
        return

    _probe_elevenlabs(api_key)


def _probe_elevenlabs(api_key: str) -> None:
    """Minimal 'hello world' against the ElevenLabs API to prove SDK wiring."""
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=api_key)
    voices = client.voices.get_all()
    print(f"ElevenLabs connected - {len(voices.voices)} voice(s) available.")


if __name__ == "__main__":
    main()
