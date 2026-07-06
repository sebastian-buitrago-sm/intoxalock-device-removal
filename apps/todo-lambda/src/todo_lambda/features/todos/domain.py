from datetime import datetime

from pydantic import BaseModel

from todo_lambda.shared.errors import ValidationError


class Todo(BaseModel):
    id: str
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls, *, id: str, title: str | None, description: str | None, created_at: datetime
    ) -> "Todo":
        trimmed_title = (title or "").strip()
        if not trimmed_title:
            raise ValidationError("title is required")
        if len(trimmed_title) > 200:
            raise ValidationError("title must be at most 200 characters")
        if description is not None and len(description) > 2000:
            raise ValidationError("description must be at most 2000 characters")

        return cls(
            id=id,
            title=trimmed_title,
            description=description,
            completed=False,
            created_at=created_at,
            updated_at=created_at,
        )
