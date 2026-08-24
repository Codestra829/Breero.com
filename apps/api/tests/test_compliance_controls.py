from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.domains.compliance.models import ConsentEvent, Suppression
from app.domains.compliance.schemas import CommunicationPreferenceCreate
from app.domains.compliance.service import ComplianceService, digest, is_revocation


@pytest.mark.parametrize(
    "message",
    ["STOP", "quit", "END", "REVOKE", "opt-out", "CANCEL", "UNSUBSCRIBE", "please stop texting"],
)
def test_sms_revocation_language_is_recognized(message: str) -> None:
    assert is_revocation(message)


def test_consent_purposes_are_separate_and_unchecked_by_default() -> None:
    preference = CommunicationPreferenceCreate(
        destination="customer@example.com",
        source_url="https://breero.com/communications-preferences",
        disclosure_text="Separate BREERO communication purpose selection.",
        policy_versions={"privacy": "2026.08.13"},
    )
    assert preference.transactionalEmail is False
    assert preference.transactionalSms is False
    assert preference.marketingEmail is False
    assert preference.marketingSms is False


def test_destination_channel_must_match_selected_purpose() -> None:
    with pytest.raises(ValidationError):
        CommunicationPreferenceCreate(
            destination="customer@example.com",
            transactionalSms=True,
            source_url="https://breero.com/communications-preferences",
            disclosure_text="Separate BREERO communication purpose selection.",
            policy_versions={"privacy": "2026.08.13"},
        )


@pytest.mark.asyncio
async def test_withdrawal_writes_hashed_consent_and_suppression() -> None:
    added = []
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=None),
        add=added.append,
        commit=AsyncMock(),
    )
    preference = CommunicationPreferenceCreate(
        destination="customer@example.com",
        source_url="https://breero.com/communications-preferences",
        disclosure_text="Separate BREERO communication purpose selection.",
        policy_versions={"privacy": "2026.08.13"},
    )
    assert await ComplianceService(session).preferences(preference, "192.0.2.4", "test-agent")
    assert all(item.destination_hash == digest("customer@example.com") for item in added)
    assert any(isinstance(item, ConsentEvent) for item in added)
    assert any(isinstance(item, Suppression) for item in added)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_explicit_reopt_in_deactivates_applicable_suppression() -> None:
    suppression = Suppression(
        destination_hash=digest("customer@example.com"),
        channel="EMAIL",
        purpose="MARKETING_EMAIL",
        reason="PREFERENCE_WITHDRAWN",
        source="PREFERENCE_CENTER",
        active=True,
    )
    session = SimpleNamespace(
        scalar=AsyncMock(side_effect=[None, suppression]),
        add=lambda _: None,
        commit=AsyncMock(),
    )
    preference = CommunicationPreferenceCreate(
        destination="customer@example.com",
        transactionalEmail=True,
        marketingEmail=True,
        source_url="https://breero.com/communications-preferences",
        disclosure_text="I explicitly opt in to these email purposes.",
        policy_versions={"privacy": "2026.08.23"},
    )

    suppression_active = await ComplianceService(session).preferences(
        preference, "192.0.2.5", "test-agent"
    )

    assert suppression.active is False
    assert suppression_active is False


def test_no_payment_route_is_mounted_while_scheduling_routes_are_mounted() -> None:
    from app.main import app

    paths = set(app.openapi()["paths"])
    assert "/api/v1/bookings" in paths
    assert "/api/v1/availability/search" in paths
    assert not any("payment" in path or "stripe" in path for path in paths)


def test_production_effective_modes_keep_marketing_and_automation_off() -> None:
    settings = Settings()
    assert settings.scheduling_enabled is True
    assert settings.automatic_booking_enabled is False
    assert settings.automatic_provider_assignment_enabled is False
    assert settings.marketing_email_enabled is False
    assert settings.marketing_sms_enabled is False
    assert settings.transactional_email_mode == "controlled_canary"
    assert settings.transactional_sms_mode == "controlled_canary"
