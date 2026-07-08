import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

_APP_ROOT = Path(__file__).resolve().parents[2]
_API_KEY_ENV = "ELEVENLABS_API_KEY"
_CONFIG_DIR_ENV = "ELEVENLABS_AGENT_CONFIG_DIR"


class Settings(BaseModel, frozen=True):
    env: str
    agent_id: str
    agent_name: str
    tags: list[str]
    phone_number_id: str
    webhook_base_url: str
    save_tool_id: str
    concurrency_limit: int
    api_key: str


def _config_dir() -> Path:
    override = os.getenv(_CONFIG_DIR_ENV)
    return Path(override) if override else _APP_ROOT / "config"


def load_settings(env: str) -> Settings:
    load_dotenv()
    config_path = _config_dir() / f"{env}.toml"
    if not config_path.is_file():
        raise FileNotFoundError(f"No config for env {env!r}: {config_path}")
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    api_key = os.getenv(_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{_API_KEY_ENV} is not set")
    return Settings.model_validate({"env": env, "api_key": api_key, **data})
