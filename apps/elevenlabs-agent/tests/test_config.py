from pathlib import Path

import pytest
from elevenlabs_agent.config import load_settings

_TOML = """
agent_id = "agent_dev_123"
agent_name = "Test Voice Agent Mindr"
tags = ["dev", "mindr"]
phone_number_id = "phnum_dev_123"
webhook_base_url = "https://dev.minder.com"
save_tool_id = "tool_dev_123"
concurrency_limit = 1
"""


def _write_config(config_dir: Path, env: str, body: str = _TOML) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / f"{env}.toml").write_text(body)


def test_load_settings_merges_toml_and_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path, "dev")
    monkeypatch.setenv("ELEVENLABS_AGENT_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("XI_API_KEY", "secret-key")

    settings = load_settings("dev")

    assert settings.env == "dev"
    assert settings.agent_id == "agent_dev_123"
    assert settings.tags == ["dev", "mindr"]
    assert settings.webhook_base_url == "https://dev.minder.com"
    assert settings.api_key == "secret-key"


def test_load_settings_requires_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_config(tmp_path, "dev")
    monkeypatch.setenv("ELEVENLABS_AGENT_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("XI_API_KEY", raising=False)
    # A real .env on the developer's machine must not leak XI_API_KEY into this test.
    monkeypatch.setattr("elevenlabs_agent.config.load_dotenv", lambda *a, **kw: False)

    with pytest.raises(RuntimeError, match="XI_API_KEY"):
        load_settings("dev")


def test_load_settings_unknown_env_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_AGENT_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("XI_API_KEY", "secret-key")

    with pytest.raises(FileNotFoundError):
        load_settings("staging")
