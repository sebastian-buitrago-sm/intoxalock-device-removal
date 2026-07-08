from elevenlabs.types import PromptAgentApiModelOutputToolsItem_Webhook
from elevenlabs_agent.definition.tools import SAVE_CALL_RESULT_TOOL_NAME, build_tools


def test_webhook_url_is_environment_scoped() -> None:
    tools = build_tools("https://dev.minder.com")
    webhook = next(t for t in tools if isinstance(t, PromptAgentApiModelOutputToolsItem_Webhook))

    assert webhook.name == SAVE_CALL_RESULT_TOOL_NAME
    api_schema = webhook.api_schema
    assert api_schema is not None
    assert api_schema.url == "https://dev.minder.com/save-call-result/{{user_id}}"


def test_definition_exposes_the_three_tools() -> None:
    names = {getattr(t, "name", None) for t in build_tools("https://x")}

    assert names == {"voicemail_detection", "end_call", SAVE_CALL_RESULT_TOOL_NAME}
