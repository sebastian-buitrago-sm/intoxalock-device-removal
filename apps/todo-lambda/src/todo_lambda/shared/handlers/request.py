import json
from typing import Any


class BadRequest(Exception):
    pass


def parse_json_object(raw: str | None) -> dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise BadRequest("Request body is not valid JSON.") from exc
    if not isinstance(value, dict):
        raise BadRequest("Request body must be a JSON object.")
    return value
