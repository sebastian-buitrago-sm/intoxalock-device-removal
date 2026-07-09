from typing import cast

from elevenlabs.client import ElevenLabs
from elevenlabs.types import WebhookHmacSettings

from elevenlabs_agent.config import Settings

_WEBHOOK_NAME = "post-call-webhook"


def post_call_webhook_url(settings: Settings) -> str:
    return f"{settings.webhook_base_url}/post-call"


def ensure_post_call_webhook(client: ElevenLabs, settings: Settings) -> str:
    """Return the workspace webhook id for settings.webhook_base_url, creating it if needed.

    Webhooks are workspace-scoped resources in ElevenLabs; an agent only ever
    references one by id (see AgentWorkspaceOverridesInput.webhooks). Reuses an
    existing webhook by URL instead of creating a duplicate each run.
    """
    webhook_url = post_call_webhook_url(settings)
    for webhook in client.webhooks.list().webhooks:
        if webhook.webhook_url == webhook_url:
            return cast(str, webhook.webhook_id)

    created = client.webhooks.create(
        settings=WebhookHmacSettings(name=_WEBHOOK_NAME, webhook_url=webhook_url),
    )
    return cast(str, created.webhook_id)
