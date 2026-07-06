from typing import Any

from core.greeting import greet


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """AWS Lambda entry point. Returns a hello-world HTTP-style response."""
    return {"statusCode": 200, "body": greet()}
