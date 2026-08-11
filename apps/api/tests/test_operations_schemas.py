import pytest
from pydantic import ValidationError

from app.domains.jobs.schemas import WorkRequestCreate
from app.domains.workforce.schemas import LocationUpdate, VendorCreate


def test_work_request_computes_from_validated_line_items():
    request = WorkRequestCreate.model_validate(
        {
            "description": "Replace failed valve",
            "line_items": [{"description": "Valve", "quantity": 2, "unit_price_minor": 1250}],
            "tax_minor": 500,
            "currency": "EUR",
        }
    )
    assert (
        sum(i.quantity * i.unit_price_minor for i in request.line_items) + request.tax_minor == 3000
    )


def test_work_request_rejects_negative_prices():
    with pytest.raises(ValidationError):
        WorkRequestCreate.model_validate(
            {
                "description": "Invalid",
                "line_items": [{"description": "Credit", "quantity": 1, "unit_price_minor": -1}],
            }
        )


def test_location_rejects_invalid_coordinates():
    with pytest.raises(ValidationError):
        LocationUpdate(latitude=91, longitude=0)


def test_vendor_requires_both_coordinates():
    with pytest.raises(ValidationError):
        VendorCreate(
            legal_name="Example GmbH",
            display_name="Example",
            email="ops@example.test",
            phone="+491234567",
            latitude=52.5,
        )
