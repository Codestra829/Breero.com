import json
import os
import secrets
import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi import HTTPException
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select

from app.api.v1.bookings import booking_confirmation, guest_booking
from app.api.v1.customers import cancel_booking
from app.api.v1.customers import payment as customer_payment
from app.db.session import SessionLocal
from app.domains.auth import models as _auth_models  # noqa: F401
from app.domains.auth.models import User
from app.domains.booking.models import (
    Address,
    Booking,
    BookingStatus,
    Customer,
    LegalEntity,
    ProviderServiceCoverage,
    ProviderWorkingHours,
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
    CompensationSnapshot,
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
from app.domains.professional_leads import models as _professional_models  # noqa: F401
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
async def test_canonical_backend_lifecycle_with_fake_providers(monkeypatch) -> None:
    marker = uuid.uuid4().hex
    service_date = (datetime.now(UTC) + timedelta(days=2)).date()
    async with SessionLocal() as session:
        entity = LegalEntity(code=f"E2E-{marker[:8]}", name="E2E Entity", currency="USD")
        session.add(entity)
        await session.flush()
        area = ServiceArea(
            legal_entity_id=entity.id,
            name="E2E Area",
            country_code="US",
            boundary=WKTElement(
                "MULTIPOLYGON(((-99 29,-97 29,-97 31,-99 31,-99 29)))", srid=4326
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
            is_bookable=True,
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
        await session.flush()
        session.add_all([
            ProviderServiceCoverage(
                worker_id=worker.id, service_id=catalog_service.id, postal_code="78701"
            ),
            ProviderWorkingHours(
                worker_id=worker.id, weekday=service_date.weekday(),
                start_time=time(7), end_time=time(19), capacity=1,
            ),
        ])
        await session.commit()

        discovered = await CatalogRepository(session).active_detail(str(catalog_service.id))
        assert discovered and discovered.questions[0].id == question.id

        geocoder = FakeGeocodingAdapter(
            GeocodedAddress(
                "E2E Street 1, Austin",
                "E2E Street 1",
                "Austin",
                "78701",
                "US",
                30.0,
                -98.0,
                "fake",
                state_code="TX",
                timezone_name="America/Chicago",
            )
        )
        validated = await AddressService(session, geocoder).validate(
            AddressValidateRequest(address="E2E Street 1, Austin")
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
        assert len(slots) == 12 and slots[0].remaining_capacity == 1
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
        assert booking.pricing_snapshot["total"] == "200.00"
        guest_token = getattr(booking, "guest_confirmation_token")
        customer = await session.get(Customer, booking.customer_id)
        assert customer
        customer_user = User(
            email=customer.email,
            password_hash="not-used-by-route-test",
            full_name="E2E Customer",
            email_verified=True,
        )
        session.add(customer_user)
        await session.flush()
        customer.user_id = customer_user.id
        cancellable = Booking(
            reference=f"CANCEL-{marker[:12]}",
            idempotency_key=f"cancel-{marker}",
            idempotency_request_hash="test",
            customer_id=customer.id,
            address_id=booking.address_id,
            legal_entity_id=booking.legal_entity_id,
            service_id=booking.service_id,
            window_start=booking.window_start + timedelta(days=1),
            window_end=booking.window_end + timedelta(days=1),
            status=BookingStatus.PENDING_PAYMENT,
            pricing_snapshot=booking.pricing_snapshot,
            total_amount=booking.total_amount,
            currency=booking.currency,
            expires_at=booking.expires_at,
            guest_confirmation_token_hash="test",
            guest_confirmation_expires_at=booking.guest_confirmation_expires_at,
        )
        session.add(cancellable)
        await session.commit()
        cancelled = await cancel_booking(cancellable.id, customer_user, session)
        assert cancelled.status == BookingStatus.CANCELLED
        cancellation_audit = await session.scalar(
            select(AuditLog).where(
                AuditLog.action == "booking.cancel", AuditLog.resource_id == cancellable.id
            )
        )
        assert cancellation_audit
        assert await guest_booking(session, booking.id, f"Bearer {guest_token}") == booking
        for invalid_booking_id, invalid_token in (
            (uuid.uuid4(), guest_token),
            (booking.id, secrets.token_urlsafe(32)),
            (booking.id, guest_token + "tampered"),
        ):
            with pytest.raises(HTTPException):
                await guest_booking(
                    session, invalid_booking_id, f"Bearer {invalid_token}"
                )
        pending_confirmation = await booking_confirmation(
            booking.id, f"Bearer {guest_token}", session, None
        )
        assert pending_confirmation.payment_status == "not_started"
        original_expiry = booking.guest_confirmation_expires_at
        booking.guest_confirmation_expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.flush()
        with pytest.raises(HTTPException) as expired:
            await guest_booking(session, booking.id, f"Bearer {guest_token}")
        assert expired.value.status_code == 403
        booking.guest_confirmation_expires_at = original_expiry
        await session.flush()

        stripe = FakeStripeProvider(marker)
        payments = PaymentService(session, stripe)
        booking_payment_view = await payments.create_intent(
            PaymentIntentCreate(
                booking_id=booking.id,
                payment_purpose=PaymentPurpose.BOOKING_DIAGNOSTIC,
                amount_minor=20000,
                currency="USD",
            ),
            f"booking-payment-{marker}",
        )
        booking_payment = await session.get(Payment, booking_payment_view.id)
        assert booking_payment
        owned_payment = await customer_payment(booking_payment.id, customer_user, session)
        assert owned_payment.id == booking_payment.id
        assert owned_payment.refunded_amount_minor == 0
        other_user = User(
            email=f"other-{marker}@example.com",
            password_hash="not-used-by-route-test",
            full_name="Other Customer",
            email_verified=True,
        )
        session.add(other_user)
        await session.flush()
        session.add(
            Customer(
                first_name="Other",
                last_name="Customer",
                email=other_user.email,
                phone="+49444444444",
                user_id=other_user.id,
            )
        )
        await session.commit()
        with pytest.raises(HTTPException) as hidden_payment:
            await customer_payment(booking_payment.id, other_user, session)
        assert hidden_payment.value.status_code == 404
        booking_payment.status = PaymentStatus.FAILED
        await session.flush()
        failed_confirmation = await booking_confirmation(
            booking.id, f"Bearer {guest_token}", session, None
        )
        assert failed_confirmation.payment_status == "failed"
        assert failed_confirmation.next_action == "retry_payment"
        booking_payment.status = PaymentStatus.REQUIRES_ACTION
        await session.flush()
        await payments.process_webhook(
            succeeded_event(f"evt-booking-{marker}", booking_payment),
            "fake-verified-signature",
        )
        await session.refresh(booking)
        assert booking.status == BookingStatus.PENDING_PROVIDER_CONFIRMATION
        confirmed = await booking_confirmation(
            booking.id, f"Bearer {guest_token}", session, None
        )
        assert confirmed.booking_status == "PENDING_PROVIDER_CONFIRMATION"
        assert confirmed.payment_status == "captured"
        assert confirmed.next_action == "await_provider_confirmation"
        job = await session.scalar(select(Job).where(Job.booking_id == booking.id))
        assert job and job.status == JobStatus.CREATED

        offers = await DispatchService(session).match(job.id)
        offer = next(item for item in offers if item.vendor_id == vendor.id)
        await DispatchService(session).decide_offer(
            offer.id, vendor.id, True, worker.id, vendor.id
        )
        await session.refresh(job)
        await session.refresh(booking)
        assert booking.status == BookingStatus.CONFIRMED
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
                    currency="USD",
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
                currency="USD",
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
                currency="USD",
                hold_days=0,
                effective_from=datetime.now(UTC) - timedelta(minutes=1),
            ),
            vendor.id,
        )
        job_id, worker_id, vendor_id = job.id, worker.id, vendor.id
        original_recognize = FinanceService.recognize_earning

        async def fail_after_earning(*args, **kwargs):
            await original_recognize(*args, **kwargs)
            raise RuntimeError("forced failure after earning creation")

        monkeypatch.setattr(FinanceService, "recognize_earning", fail_after_earning)
        with pytest.raises(RuntimeError, match="forced failure"):
            await jobs.technician_note_transition(
                job.id,
                worker.id,
                worker.id,
                "completion_notes",
                "Repair complete",
                JobStatus.COMPLETED,
            )
        await session.rollback()
        rolled_back_job = await session.get(Job, job_id)
        booking_payment = await session.get(Payment, booking_payment_view.id)
        quote_payment = await session.get(Payment, quote_payment_view.id)
        assert rolled_back_job and rolled_back_job.status == JobStatus.IN_PROGRESS
        assert booking_payment and quote_payment
        assert await session.scalar(
            select(func.count()).select_from(VendorEarning).where(VendorEarning.job_id == job_id)
        ) == 0
        assert await session.scalar(
            select(func.count()).select_from(CompensationSnapshot).where(
                CompensationSnapshot.vendor_id == vendor_id
            )
        ) == 0
        assert await session.scalar(
            select(func.count()).select_from(IntegrationEvent).where(
                IntegrationEvent.aggregate_id == job_id,
                IntegrationEvent.event_type == "job.completed",
            )
        ) == 0
        monkeypatch.setattr(FinanceService, "recognize_earning", original_recognize)
        await jobs.technician_note_transition(
            job_id, worker_id, worker_id, "completion_notes", "Repair complete", JobStatus.COMPLETED
        )
        job = await session.get(Job, job_id)
        earning = await session.scalar(select(VendorEarning).where(VendorEarning.job_id == job_id))
        assert earning and earning.net_minor == 7000 and earning.status == EarningStatus.PENDING
        assert await session.scalar(
            select(func.count()).select_from(VendorEarning).where(VendorEarning.job_id == job_id)
        ) == 1
        assert await finance.release_eligible() == 1
        batch = await finance.create_batch("USD", vendor_id, vendor_id)
        assert batch.status == PayoutStatus.PENDING_APPROVAL and batch.earning_count == 1
        await finance.approve_batch(batch.id, vendor_id)
        submitted = await finance.submit_batch(batch.id, vendor_id)
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
