from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from todo_lambda.shared.domain import ValidationError


class Todo(BaseModel):
    id: str
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("title", mode="before")
    @classmethod
    def _trim_title(cls, value: str | None) -> str:
        return (value or "").strip()

    @model_validator(mode="after")
    def _title_and_description_differ(self) -> "Todo":
        if self.description is not None and self.title == self.description:
            raise ValidationError("title and description must differ")
        return self
