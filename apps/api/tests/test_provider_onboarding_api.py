import uuid

import pytest
from pydantic import ValidationError

from app.api.v1.router import api_router
from app.domains.workforce.models import ProviderApplication, ProviderApplicationStatus
from app.domains.workforce.onboarding_service import ProviderOnboardingService
from app.domains.workforce.schemas import (
    ProviderApplicationDecision,
    ProviderOnboardingUpdate,
)


def route_contract() -> set[tuple[str, str]]:
    return {
        (route.path, method)
        for route in api_router.routes
        for method in getattr(route, "methods", set())
    }


def test_provider_onboarding_routes_are_registered() -> None:
    required = {
        ("/auth/register/provider", "POST"),
        ("/provider/profile", "GET"),
        ("/provider/profile", "PATCH"),
        ("/provider/onboarding", "GET"),
        ("/provider/onboarding", "PATCH"),
        ("/provider/onboarding/submit", "POST"),
        ("/admin/provider-applications", "GET"),
        ("/admin/provider-applications/{application_id}", "GET"),
        ("/admin/provider-applications/{application_id}/approve", "POST"),
        ("/admin/provider-applications/{application_id}/reject", "POST"),
        (
            "/admin/provider-applications/{application_id}/request-information",
            "POST",
        ),
    }
    assert required.issubset(route_contract())


def test_onboarding_patch_rejects_status_and_vendor_mass_assignment() -> None:
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate.model_validate({"status": "APPROVED"})
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate.model_validate({"vendor_id": str(uuid.uuid4())})


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
