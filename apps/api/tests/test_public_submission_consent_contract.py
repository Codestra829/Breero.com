import pytest
from pydantic import ValidationError

from app.domains.public_submissions.schemas import ContactCreate


BASE_CONTACT = {
    "name": "Consent Customer",
    "email": "consent@example.com",
    "category": "general",
    "subject": "Consent question",
    "message": "This is a valid consent-contract test message.",
    "source_url": "https://breero.com/contact",
    "transactional_contact_allowed": True,
}


def test_optional_channel_consent_requires_matching_disclosure_evidence() -> None:
    with pytest.raises(ValidationError, match="transactional_sms"):
        ContactCreate(
            **BASE_CONTACT,
            transactional_sms_consent=True,
            policy_version="2026-08-13-request-only",
        )


def test_optional_channel_consent_requires_policy_version() -> None:
    with pytest.raises(ValidationError, match="policy version"):
        ContactCreate(
            **BASE_CONTACT,
            marketing_email_consent=True,
            consent_disclosures={
                "marketing_email": "I separately agree to receive BREERO marketing email."
            },
        )


def test_channel_specific_consent_accepts_complete_versioned_evidence() -> None:
    contact = ContactCreate(
        **BASE_CONTACT,
        transactional_email_consent=True,
        transactional_sms_consent=True,
        marketing_email_consent=True,
        marketing_sms_consent=True,
        policy_version="2026-08-13-request-only",
        consent_disclosures={
            "transactional_email": "I agree to receive request and service-status email.",
            "transactional_sms": "I agree to receive request and service-status text messages.",
            "marketing_email": "I separately agree to receive marketing email.",
            "marketing_sms": "I separately agree to receive marketing text messages.",
        },
    )

    assert contact.transactional_sms_consent is True
    assert contact.marketing_sms_consent is True
    assert set(contact.consent_disclosures) == {
        "transactional_email",
        "transactional_sms",
        "marketing_email",
        "marketing_sms",
    }


def test_legacy_aggregate_consent_flags_are_rejected() -> None:
    for flag in ("email_consent", "sms_consent", "marketing_consent"):
        with pytest.raises(ValidationError, match="Legacy aggregate consent"):
            ContactCreate(**BASE_CONTACT, **{flag: True})


def test_no_optional_channel_consent_does_not_require_disclosures() -> None:
    contact = ContactCreate(**BASE_CONTACT)

    assert contact.consent_disclosures == {}
    assert contact.transactional_email_consent is False
    assert contact.transactional_sms_consent is False
