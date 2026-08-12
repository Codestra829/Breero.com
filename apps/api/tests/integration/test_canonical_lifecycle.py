import json
import os
import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Any

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from app.db.session import SessionLocal
from app.domains.auth import models as _auth_models  # noqa: F401
from app.domains.booking.models import (
    Address,
    AvailabilityRule,
    BookingStatus,
    LegalEntity,
    ServiceArea,
)
from app.domains.booking.schemas import (
    AddressValidateRequest,
    AvailabilitySearchRequest,
    BookingAnswerInput,
    BookingCreateRequest,
    BookingWindow,
    CustomerInput,
)
from app.domains.booking.service import AddressService, AvailabilityService, BookingService
from app.domains.catalog.models import QuestionType, Service, ServiceQuestion
from app.domains.catalog.repository import CatalogRepository
from app.domains.common.outbox import AuditLog, EventStatus, IntegrationEvent
from app.domains.common.outbox_service import OutboxService
from app.domains.dispatch.service import DispatchService
from app.domains.finance.models import (
    CompensationMethod,
    EarningStatus,
    PayoutStatus,
    VendorEarning,
)
from app.domains.finance.schemas import CompensationPlanCreate
from app.domains.finance.service import FinanceService
from app.domains.jobs.models import Job, JobStatus, WorkRequestStatus
from app.domains.jobs.schemas import WorkLineItem, WorkRequestCreate
from app.domains.jobs.service import JobService
from app.domains.payments.models import Payment, PaymentPurpose, PaymentStatus
from app.domains.payments.schemas import PaymentIntentCreate, ProviderIntent, ProviderRefund
from app.domains.payments.service import PaymentService
from app.domains.workforce.models import Vendor, VendorStatus, Worker, WorkerStatus
from app.integrations.geocoding import FakeGeocodingAdapter, GeocodedAddress
from app.integrations.odoo import MAPPERS
from app.integrations.payouts import FakePayoutGateway

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="canonical lifecycle requires PostgreSQL/PostGIS",
)


class FakeStripeProvider:
    def __init__(self, marker: str) -> None:
        self.counter = 0
        self.marker = marker

    async def create_intent(self, **_: Any) -> ProviderIntent:
        self.counter += 1
        return ProviderIntent(
            id=f"pi_e2e_{self.marker}_{self.counter}",
            status="requires_action",
            client_secret=f"secret_e2e_{self.counter}",
        )

    async def capture_intent(self, provider_payment_id: str, **_: Any) -> ProviderIntent:
        return ProviderIntent(id=provider_payment_id, status="succeeded", amount_received=1)

    def verify_webhook(self, body: bytes, signature: str) -> dict[str, Any]:
        assert signature == "fake-verified-signature"
        return json.loads(body)

    async def create_refund(self, provider_payment_id: str, **_: Any) -> ProviderRefund:
        return ProviderRefund(id=f"re_{provider_payment_id}", status="succeeded")


def succeeded_event(event_id: str, payment: Payment) -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "object": "payment_intent",
                    "id": payment.provider_payment_id,
                    "status": "succeeded",
                    "amount_received": payment.amount_minor,
                }
            },
        }
    ).encode()


@pytest.mark.asyncio
async def test_canonical_backend_lifecycle_with_fake_providers() -> None:
    marker = uuid.uuid4().hex
    service_date = (datetime.now(UTC) + timedelta(days=2)).date()
    async with SessionLocal() as session:
        entity = LegalEntity(code=f"E2E-{marker[:8]}", name="E2E Entity", currency="EUR")
        session.add(entity)
        await session.flush()
        area = ServiceArea(
            legal_entity_id=entity.id,
            name="E2E Area",
            boundary=WKTElement(
                "MULTIPOLYGON(((12 51,14 51,14 53,12 53,12 51)))", srid=4326
            ),
            active=True,
        )
        catalog_service = Service(
            slug=f"e2e-service-{marker}",
            name="E2E Repair",
            description="Canonical lifecycle service",
            base_price=Decimal("129.00"),
            duration_minutes=120,
            is_active=True,
        )
        session.add_all([area, catalog_service])
        await session.flush()
        question = ServiceQuestion(
            service_id=catalog_service.id,
            key="symptom",
            label="What is wrong?",
            question_type=QuestionType.text,
            required=True,
            sort_order=1,
            is_active=True,
        )
        session.add(
            AvailabilityRule(
                service_id=catalog_service.id,
                service_area_id=area.id,
                weekday=service_date.weekday(),
                start_time=time(9),
                end_time=time(11),
                slot_minutes=120,
                capacity=1,
            )
        )
        session.add(question)
        vendor = Vendor(
            legal_name="E2E Vendor GmbH",
            display_name="E2E Vendor",
            email=f"vendor-{marker}@example.test",
            phone="+49111111111",
            status=VendorStatus.ACTIVE,
            capabilities=[],
            payout_profile_ref=f"fake-{marker}",
        )
        session.add(vendor)
        await session.flush()
        worker = Worker(
            vendor_id=vendor.id,
            first_name="E2E",
            last_name="Technician",
            email=f"worker-{marker}@example.test",
            phone="+49222222222",
            status=WorkerStatus.ACTIVE,
            skills=[],
            available=True,
        )
        session.add(worker)
        await session.commit()

        discovered = await CatalogRepository(session).active_detail(str(catalog_service.id))
        assert discovered and discovered.questions[0].id == question.id

        geocoder = FakeGeocodingAdapter(
            GeocodedAddress(
                "E2E Street 1, Berlin",
                "E2E Street 1",
                "Berlin",
                "10115",
                "DE",
                52.0,
                13.0,
                "fake",
            )
        )
        validated = await AddressService(session, geocoder).validate(
            AddressValidateRequest(address="E2E Street 1, Berlin")
        )
        assert validated.serviceable and validated.address_id
        # Multiple runs may leave overlapping test polygons; bind this run's validated address to
        # its own service-area fixture after proving the PostGIS lookup is serviceable.
        validated_address = await session.get(Address, validated.address_id)
        assert validated_address
        validated_address.service_area_id = area.id
        await session.commit()

        slots = await AvailabilityService(session).search(
            AvailabilitySearchRequest(
                service_id=catalog_service.id,
                address_id=validated.address_id,
                date_from=service_date,
                date_to=service_date,
            )
        )
        assert len(slots) == 1 and slots[0].remaining_capacity == 1
        booking = await BookingService(session).create(
            BookingCreateRequest(
                service_id=catalog_service.id,
                customer=CustomerInput(
                    first_name="E2E",
                    last_name="Customer",
                    email=f"customer-{marker}@example.com",
                    phone="+49333333333",
                ),
                address_id=validated.address_id,
                window=BookingWindow(start=slots[0].start, end=slots[0].end),
                answers=[BookingAnswerInput(question_id=question.id, value="No heat")],
            ),
            f"booking-{marker}",
        )
        assert booking.status == BookingStatus.PENDING_PAYMENT
        assert booking.pricing_snapshot["total"] == "129.00"

        stripe = FakeStripeProvider(marker)
        payments = PaymentService(session, stripe)
        booking_payment_view = await payments.create_intent(
            PaymentIntentCreate(
                booking_id=booking.id,
                payment_purpose=PaymentPurpose.BOOKING_DIAGNOSTIC,
                amount_minor=12900,
                currency="EUR",
            ),
            f"booking-payment-{marker}",
        )
        booking_payment = await session.get(Payment, booking_payment_view.id)
        assert booking_payment
        await payments.process_webhook(
            succeeded_event(f"evt-booking-{marker}", booking_payment),
            "fake-verified-signature",
        )
        await session.refresh(booking)
        assert booking.status == BookingStatus.CONFIRMED
        job = await session.scalar(select(Job).where(Job.booking_id == booking.id))
        assert job and job.status == JobStatus.CREATED

        offers = await DispatchService(session).match(job.id)
        offer = next(item for item in offers if item.vendor_id == vendor.id)
        await DispatchService(session).decide_offer(
            offer.id, vendor.id, True, worker.id, vendor.id
        )
        await session.refresh(job)
        assert job.status == JobStatus.ASSIGNED and job.worker_id == worker.id

        jobs = JobService(session)
        await jobs.transition(job.id, JobStatus.EN_ROUTE, worker.id, "worker")
        await jobs.transition(job.id, JobStatus.ON_SITE, worker.id, "worker")
        await jobs.technician_note_transition(
            job.id, worker.id, worker.id, "diagnostic_notes", "Pump failure", JobStatus.DIAGNOSING
        )
        request = await jobs.create_work_request(
            job.id,
            WorkRequestCreate(
                description="Replace pump",
                line_items=[
                    WorkLineItem(description="Replacement pump", quantity=1, unit_price_minor=5000)
                ],
                tax_minor=950,
                currency="EUR",
            ),
            worker.id,
        )
        await jobs.review_work_request(request.id, True)
        await jobs.decide_work_request(request.id, True, booking.customer_id)
        assert request.status == WorkRequestStatus.APPROVED_PENDING_PAYMENT

        quote_payment_view = await payments.create_intent(
            PaymentIntentCreate(
                quote_id=request.id,
                payment_purpose=PaymentPurpose.QUOTE_ADDITIONAL_WORK,
                amount_minor=5950,
                currency="EUR",
            ),
            f"quote-payment-{marker}",
        )
        quote_payment = await session.get(Payment, quote_payment_view.id)
        assert quote_payment
        await payments.process_webhook(
            succeeded_event(f"evt-quote-{marker}", quote_payment), "fake-verified-signature"
        )
        await session.refresh(job)
        assert request.status == WorkRequestStatus.APPROVED and job.status == JobStatus.IN_PROGRESS

        finance = FinanceService(session, FakePayoutGateway())
        await finance.create_compensation_plan(
            CompensationPlanCreate(
                vendor_id=vendor.id,
                name="E2E fixed plan",
                method=CompensationMethod.FIXED_MINOR,
                fixed_minor=7000,
                currency="EUR",
                hold_days=0,
                effective_from=datetime.now(UTC) - timedelta(minutes=1),
            ),
            vendor.id,
        )
        await jobs.technician_note_transition(
            job.id, worker.id, worker.id, "completion_notes", "Repair complete", JobStatus.COMPLETED
        )
        earning = await session.scalar(select(VendorEarning).where(VendorEarning.job_id == job.id))
        assert earning and earning.net_minor == 7000 and earning.status == EarningStatus.PENDING
        assert await finance.release_eligible() == 1
        batch = await finance.create_batch("EUR", vendor.id, vendor.id)
        assert batch.status == PayoutStatus.PENDING_APPROVAL and batch.earning_count == 1
        await finance.approve_batch(batch.id, vendor.id)
        submitted = await finance.submit_batch(batch.id, vendor.id)
        assert submitted.status == PayoutStatus.PROCESSING
        assert submitted.provider_transfer_id.startswith("fake_")

        delivered: list[str] = []

        async def fake_odoo(event: IntegrationEvent) -> None:
            mapper = MAPPERS.get(event.aggregate_type)
            if mapper:
                mapper.map(event.payload)
            delivered.append(event.event_type)

        processed = await OutboxService(session).process(fake_odoo, limit=100)
        assert processed >= 5
        assert "payout.submitted" in delivered and "job.completed" in delivered
        remaining = await session.scalar(
            select(IntegrationEvent).where(
                IntegrationEvent.aggregate_id == submitted.id,
                IntegrationEvent.status != EventStatus.DELIVERED,
            )
        )
        assert remaining is None
        assert booking_payment.status == PaymentStatus.CAPTURED
        assert quote_payment.status == PaymentStatus.CAPTURED
        audit_actions = set((await session.scalars(select(AuditLog.action))).all())
        assert {"assignment.create", "quote.approve", "compensation_plan.change", "payout.approve"} <= audit_actions
