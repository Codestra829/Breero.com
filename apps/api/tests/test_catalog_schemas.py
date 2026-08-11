import pytest
from pydantic import ValidationError

from app.domains.catalog.schemas import QuestionWrite, ServiceWrite


def test_choice_question_requires_options() -> None:
    with pytest.raises(ValidationError):
        QuestionWrite(key="property_type", label="Property type", question_type="single_choice")


def test_service_write_validates_booking_constraints() -> None:
    service = ServiceWrite(
        slug="air-conditioning", name="Air conditioning", base_price="99.00", duration_minutes=60
    )
    assert service.slug == "air-conditioning"
    assert service.questions == []
