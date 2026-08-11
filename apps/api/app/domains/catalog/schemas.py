import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.catalog.models import QuestionType


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    key: str
    label: str
    help_text: str | None
    question_type: QuestionType
    required: bool
    options: list[dict] | None
    validation: dict | None
    sort_order: int


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    base_price: Decimal
    duration_minutes: int


class ServiceDetail(ServiceRead):
    questions: list[QuestionRead]


class QuestionWrite(BaseModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{1,99}$")
    label: str = Field(min_length=1, max_length=240)
    help_text: str | None = None
    question_type: QuestionType
    required: bool = False
    options: list[dict] | None = None
    validation: dict | None = None
    sort_order: int = 0

    @model_validator(mode="after")
    def choices_require_options(self) -> "QuestionWrite":
        if (
            self.question_type in {QuestionType.single_choice, QuestionType.multi_choice}
            and not self.options
        ):
            raise ValueError("Choice questions require options")
        return self


class ServiceWrite(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    base_price: Decimal = Field(ge=0)
    duration_minutes: int = Field(ge=15, le=1440)
    sort_order: int = 0
    questions: list[QuestionWrite] = Field(default_factory=list)
