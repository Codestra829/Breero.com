import uuid

import pytest
from pydantic import ValidationError

from app.domains.workforce.models import (
    ProviderApplication,
    ProviderApplicationStatus,
)
from app.domains.workforce.onboarding_service import ProviderOnboardingService
from app.domains.workforce.schemas import (
    ProviderApplicationDecision,
    ProviderOnboardingUpdate,
)
from app.main import app


def test_provider_onboarding_routes_are_registered() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/api/v1/auth/register/provider": {"post"},
        "/api/v1/provider/profile": {"get", "patch"},
        "/api/v1/provider/onboarding": {"get", "patch"},
        "/api/v1/provider/onboarding/submit": {"post"},
        "/api/v1/admin/provider-applications": {"get"},
        "/api/v1/admin/provider-applications/{application_id}": {"get"},
        "/api/v1/admin/provider-applications/{application_id}/approve": {"post"},
        "/api/v1/admin/provider-applications/{application_id}/reject": {"post"},
        (
            "/api/v1/admin/provider-applications/"
            "{application_id}/request-information"
        ): {"post"},
    }
    for path, methods in required.items():
        assert methods <= set(paths[path])


def test_onboarding_patch_rejects_status_and_vendor_mass_assignment() -> None:
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate.model_validate({"status": "APPROVED"})
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate.model_validate(
            {"vendor_id": str(uuid.uuid4())}
        )


def test_postal_codes_validate_zip_and_zip4() -> None:
    payload = ProviderOnboardingUpdate(
        postal_codes=["02108", "02108-1234", "02108"]
    )
    assert payload.postal_codes == ["02108", "02108-1234"]
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate(postal_codes=["ABC12"])
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate(postal_codes=["021081234"])


def test_submission_requires_every_mission_domain() -> None:
    application = ProviderApplication(
        id=uuid.uuid4(),
        vendor_id=uuid.uuid4(),
        status=ProviderApplicationStatus.DRAFT,
        identity={"legal_name": "Owner"},
        business={},
        contact_details={},
        services=[],
        skills=[],
        service_areas=[],
        postal_codes=[],
        availability={},
        capacity={},
        licenses=[],
        insurance=[],
        compliance_documents=[],
        version=1,
    )
    assert ProviderOnboardingService.missing_submission_fields(application) == [
        "business",
        "contact_details",
        "services",
        "skills",
        "service_areas",
        "postal_codes",
        "availability",
        "capacity",
        "licenses",
        "insurance",
        "compliance_documents",
    ]


def test_complete_application_has_no_missing_submission_domains() -> None:
    application = ProviderApplication(
        id=uuid.uuid4(),
        vendor_id=uuid.uuid4(),
        status=ProviderApplicationStatus.DRAFT,
        identity={"owner": "Owner"},
        business={"legal_name": "Provider LLC"},
        contact_details={"phone": "+15551234567"},
        services=[str(uuid.uuid4())],
        skills=["plumbing"],
        service_areas=[{"type": "ZIP", "value": "02108"}],
        postal_codes=["02108"],
        availability={"monday": [["07:00", "19:00"]]},
        capacity={"daily_jobs": 4, "daily_minutes": 480},
        licenses=[{"type": "trade", "jurisdiction": "MA"}],
        insurance=[{"type": "general_liability"}],
        compliance_documents=[str(uuid.uuid4())],
        version=1,
    )
    assert not ProviderOnboardingService.missing_submission_fields(application)


def test_provider_application_decision_requires_reason() -> None:
    with pytest.raises(ValidationError):
        ProviderApplicationDecision(reason="no")
