import json
from typing import Any

from todo_lambda.shared.errors import DomainError


def problem_response(error: DomainError) -> dict[str, Any]:
    body = {"status": error.status_code, "title": str(error)}
    return {
        "statusCode": error.status_code,
        "headers": {"Content-Type": "application/problem+json"},
        "body": json.dumps(body),
    }
