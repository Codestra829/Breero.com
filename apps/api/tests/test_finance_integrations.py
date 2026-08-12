import uuid
from types import SimpleNamespace

import pytest

from app.domains.finance.compensation import calculate_compensation
from app.domains.finance.models import CompensationMethod
from app.integrations.email import FakeEmailGateway, render_email
from app.integrations.geocoding import FakeGeocodingAdapter, GeocodedAddress
from app.integrations.odoo import (
    BookingOdooMapper,
    CustomerOdooMapper,
    JobOdooMapper,
    PaymentOdooMapper,
    PayoutOdooMapper,
    VendorOdooMapper,
)
from app.integrations.payouts import FakePayoutGateway
from app.integrations.sms import FakeSmsGateway, render_sms


def plan(method, fixed_minor=None, percentage_bps=None):
    return SimpleNamespace(method=method, fixed_minor=fixed_minor, percentage_bps=percentage_bps)


def test_percentage_compensation_is_deterministic_snapshot_input():
    configured = plan(CompensationMethod.PERCENTAGE, percentage_bps=6250)
    calculated = calculate_compensation(configured, 10_001)
    assert calculated.amount_minor == 6250
    assert calculated.rule == {"percentage_bps": 6250}
    configured.percentage_bps = 5000
    assert calculated.amount_minor == 6250


def test_all_compensation_methods():
    assert calculate_compensation(plan(CompensationMethod.FIXED_MINOR, 2400), 9999).amount_minor == 2400
    service = SimpleNamespace(rate_minor=3300, service_id=uuid.uuid4())
    assert calculate_compensation(plan(CompensationMethod.SERVICE_RATE), 9999, service).amount_minor == 3300


@pytest.mark.asyncio
async def test_fake_payout_is_idempotent():
    gateway = FakePayoutGateway()
    values = dict(amount_minor=1000, currency="USD", destination="vendor:1", idempotency_key="same")
    first = await gateway.create_transfer(**values)
    second = await gateway.create_transfer(**values)
    assert first.transfer_id == second.transfer_id
    assert len(gateway.transfers) == 1


@pytest.mark.asyncio
async def test_provider_success_then_application_crash_retry_creates_one_transfer():
    gateway = FakePayoutGateway()
    values = dict(
        amount_minor=1000,
        currency="USD",
        destination="batch:crash-test",
        idempotency_key="payout-batch:stable-crash-key",
    )
    succeeded_before_crash = await gateway.create_transfer(**values)
    # The application dies before persisting the transfer ID. A retry has only the stable key.
    recovered = await gateway.create_transfer(**values)
    assert recovered.transfer_id == succeeded_before_crash.transfer_id
    assert len(gateway.transfers) == 1


def test_odoo_mappers_have_explicit_models_and_identifiers():
    identifier = uuid.uuid4()
    assert CustomerOdooMapper().model == "res.partner"
    assert CustomerOdooMapper().map({"id": identifier, "first_name": "A", "last_name": "B"})["ref"] == str(identifier)
    assert VendorOdooMapper().model == "res.partner"
    assert BookingOdooMapper().model == "sale.order"
    assert JobOdooMapper().model == "project.task"
    assert PaymentOdooMapper().model == "account.payment"
    assert PayoutOdooMapper().map({"total_minor": 1234})["amount"] == 12.34


@pytest.mark.asyncio
async def test_fake_email_and_sms():
    email, sms = FakeEmailGateway(), FakeSmsGateway()
    rendered = render_email("booking.confirmed")
    await email.send(to="customer@example.test", subject=rendered.subject, text=rendered.text)
    await sms.send(to="+15550000000", text=render_sms("technician.on_the_way"))
    assert len(email.sent) == len(sms.sent) == 1


@pytest.mark.asyncio
async def test_fake_geocoder():
    expected = GeocodedAddress("1 Main St", "1 Main St", "Austin", "78701", "US", 1, 2, "fake", "x", 1.0, "exact")
    assert await FakeGeocodingAdapter(expected).geocode("anything") == expected
