import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from geoalchemy2.elements import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.booking.models import Address, Booking, BookingAnswer, BookingStatus, Customer
from app.domains.booking.repository import BookingRepository
from app.domains.booking.schemas import (
    AddressValidateRequest,
    AddressValidationResponse,
    AvailabilitySearchRequest,
    AvailabilitySlot,
    BookingCreateRequest,
)
from app.domains.catalog.repository import CatalogRepository
from app.domains.common.outbox import EventStatus, IntegrationEvent
from app.domains.jobs.models import Job, JobEvent, JobStatus
from app.integrations.geocoding import GeocodedAddress, GeocodingAdapter


class AddressService:
    def __init__(self, session: AsyncSession, geocoder: GeocodingAdapter | None = None) -> None:
        self.session = session
        self.repository = BookingRepository(session)
        self.geocoder = geocoder or GeocodingAdapter()

    async def validate(self, payload: AddressValidateRequest) -> AddressValidationResponse:
        if payload.latitude is None or payload.longitude is None:
            resolved = await self.geocoder.geocode(payload.address)
        else:
            resolved = GeocodedAddress(
                formatted_address=payload.address,
                line1=payload.line1 or payload.address,
                city=payload.city or "",
                state_code=payload.state_code.upper() if payload.state_code else None,
                postal_code=payload.postal_code or "",
                country_code=payload.country_code.upper(),
                latitude=payload.latitude,
                longitude=payload.longitude,
                provider="provided",
                timezone=payload.timezone,
            )
        if not resolved.postal_code or not resolved.state_code or not resolved.city:
            raise DomainError("ADDRESS_INCOMPLETE", "Street, city, state, and ZIP are required", 422)
        if resolved.country_code != "US":
            raise DomainError(
                "ADDRESS_COUNTRY_UNSUPPORTED", "Only United States addresses are supported", 422
            )
        timezone_name = resolved.timezone or payload.timezone
        try:
            if not timezone_name:
                raise ZoneInfoNotFoundError
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise DomainError(
                "ADDRESS_TIMEZONE_UNRESOLVED",
                "The service-address time zone could not be resolved; manual dispatch is required",
                422,
            ) from exc
        match = await self.repository.service_area_at(resolved.longitude, resolved.latitude)
        area, entity = match if match else (None, None)
        address = Address(
            formatted_address=resolved.formatted_address,
            line1=resolved.line1,
            city=resolved.city,
            state_code=resolved.state_code,
            postal_code=resolved.postal_code,
            country_code=resolved.country_code,
            service_area_id=area.id if area else None,
            geocoding_provider=resolved.provider,
            timezone=timezone_name,
            validated_at=datetime.now(UTC),
            location=WKTElement(f"POINT({resolved.longitude} {resolved.latitude})", srid=4326),
        )
        await self.repository.add_address(address)
        await self.session.commit()
        return AddressValidationResponse(
            serviceable=bool(area),
            formatted_address=address.formatted_address,
            address_id=address.id,
            service_area_id=area.id if area else None,
            legal_entity_code=entity.code if entity else None,
            timezone=timezone_name,
            manual_dispatch_required=not bool(area),
        )


class AvailabilityService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = BookingRepository(session)

    async def search(self, payload: AvailabilitySearchRequest) -> list[AvailabilitySlot]:
        address = await self.repository.address(payload.address_id)
        if not address or not address.service_area_id:
            raise DomainError(
                "ADDRESS_NOT_SERVICEABLE", "Address is outside an active service area", 422
            )
        rules = await self.repository.availability_rules(
            payload.service_id, address.service_area_id
        )
        slots: list[AvailabilitySlot] = []
        current = payload.date_from
        while current <= payload.date_to:
            for rule in rules:
                if (
                    rule.weekday != current.weekday()
                    or rule.active_from
                    and current < rule.active_from
                    or rule.active_to
                    and current > rule.active_to
                ):
                    continue
                zone = ZoneInfo(address.timezone or "UTC")
                cursor = datetime.combine(current, rule.start_time, tzinfo=zone).astimezone(UTC)
                boundary = datetime.combine(current, rule.end_time, tzinfo=zone).astimezone(UTC)
                while cursor + timedelta(minutes=rule.slot_minutes) <= boundary:
                    end = cursor + timedelta(minutes=rule.slot_minutes)
                    used = await self.repository.booking_count(payload.service_id, cursor, end)
                    if used < rule.capacity:
                        slots.append(
                            AvailabilitySlot(
                                start=cursor, end=end, remaining_capacity=rule.capacity - used
                            )
                        )
                    cursor = end
            current += timedelta(days=1)
        return slots


class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = BookingRepository(session)
        self.availability = AvailabilityService(session)

    async def create(self, payload: BookingCreateRequest, idempotency_key: str) -> Booking:
        request_hash = hashlib.sha256(
            json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        await self.repository.lock_idempotency_key(idempotency_key)
        existing = await self.repository.booking_by_idempotency_key(idempotency_key)
        if existing:
            if existing.idempotency_request_hash not in {"legacy", request_hash}:
                raise DomainError(
                    "IDEMPOTENCY_CONFLICT",
                    "The idempotency key was already used for a different booking request",
                    409,
                )
            return existing
        if payload.window.start >= payload.window.end or payload.window.start <= datetime.now(UTC):
            raise DomainError("INVALID_BOOKING_WINDOW", "Booking window must be in the future", 422)
        address = await self.repository.address(payload.address_id)
        if not address or not address.validated_at or not address.timezone:
            raise DomainError("ADDRESS_NOT_VALIDATED", "Address and time zone must be validated", 422)
        zone = ZoneInfo(address.timezone)
        local_start = payload.window.start.astimezone(zone)
        local_end = payload.window.end.astimezone(zone)
        if local_start.date() != local_end.date() or local_start.hour < 7 or local_end.hour > 19:
            raise DomainError(
                "OUTSIDE_SERVICE_HOURS",
                "Requested time must be between 7:00 AM and 7:00 PM local time",
                422,
            )
        if local_start.weekday() == 6 and not payload.urgent:
            raise DomainError(
                "SUNDAY_EMERGENCY_ONLY",
                "Sunday requests must be urgent home-service requests",
                422,
            )
        entity = None
        slot_available = False
        if address.service_area_id:
            await self.repository.lock_slot(
                payload.service_id, payload.window.start, payload.window.end
            )
            slots = await self.availability.search(
                AvailabilitySearchRequest(
                    service_id=payload.service_id,
                    address_id=payload.address_id,
                    date_from=local_start.date(),
                    date_to=local_start.date(),
                )
            )
            slot_available = any(
                slot.start == payload.window.start and slot.end == payload.window.end
                for slot in slots
            )
            entity = await self.repository.legal_entity_for_area(address.service_area_id)
        service = await CatalogRepository(self.session).active_detail(str(payload.service_id))
        if not service:
            raise DomainError("SERVICE_NOT_FOUND", "Service is not available", 404)
        if not service.is_bookable:
            raise DomainError("SERVICE_NOT_BOOKABLE", "Service is not currently bookable", 422)
        supplied = {answer.question_id for answer in payload.answers}
        required = {
            question.id
            for question in service.questions
            if question.is_active and question.required
        }
        if missing := required - supplied:
            raise DomainError(
                "REQUIRED_ANSWERS_MISSING", f"Missing {len(missing)} required answer(s)", 422
            )
        valid_questions = {question.id for question in service.questions if question.is_active}
        if supplied - valid_questions:
            raise DomainError(
                "INVALID_QUESTION", "An answer references an invalid service question", 422
            )
        # Catalog pricing is copied into an immutable snapshot; never recomputed for an existing booking.
        amount = service.base_price or 0
        customer = await self.repository.customer_for_email(str(payload.customer.email).lower())
        if customer is None:
            customer = Customer(
                first_name=payload.customer.first_name,
                last_name=payload.customer.last_name,
                email=str(payload.customer.email).lower(),
                phone=payload.customer.phone,
            )
            await self.repository.add(customer)
        if customer.user_id and address.customer_id is None:
            address.customer_id = customer.id
        booking = Booking(
            reference=f"BR-{secrets.token_hex(5).upper()}",
            idempotency_key=idempotency_key,
            idempotency_request_hash=request_hash,
            customer_id=customer.id,
            address_id=address.id,
            legal_entity_id=entity.id if entity else None,
            service_id=payload.service_id,
            window_start=payload.window.start,
            window_end=payload.window.end,
            status=(
                BookingStatus.TENTATIVE_HOLD
                if slot_available
                else BookingStatus.PENDING_MANUAL_DISPATCH
            ),
            pricing_snapshot={
                "service_id": str(payload.service_id),
                "service_name": service.name,
                "base_price": str(amount),
                "total": str(amount),
                "currency": entity.currency if entity else "USD",
                "quote_required": True,
                "payment_required": False,
                "urgent": payload.urgent,
            },
            total_amount=amount,
            currency=entity.currency if entity else "USD",
            expires_at=datetime.now(UTC) + timedelta(hours=24),
            hold_expires_at=(
                datetime.now(UTC) + timedelta(minutes=15) if slot_available else None
            ),
            guest_confirmation_token_hash="pending",
            guest_confirmation_expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        guest_token = secrets.token_urlsafe(32)
        booking.guest_confirmation_token_hash = hashlib.sha256(guest_token.encode()).hexdigest()
        await self.repository.add(booking)
        job = Job(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            service_id=booking.service_id,
            address_id=booking.address_id,
            status=JobStatus.CREATED,
            scheduled_start=booking.window_start,
            scheduled_end=booking.window_end,
            version=1,
        )
        await self.repository.add(job)
        await self.repository.add(
            JobEvent(
                job_id=job.id,
                from_status=None,
                to_status=JobStatus.CREATED,
                actor_id=None,
                actor_type="customer",
                reason="quote_only_service_requested",
            )
        )
        await self.repository.add(
            IntegrationEvent(
                aggregate_type="booking",
                aggregate_id=booking.id,
                event_type="booking.requested",
                idempotency_key=f"booking.requested:{booking.id}:1",
                payload={
                    "booking_id": str(booking.id),
                    "job_id": str(job.id),
                    "status": booking.status.value,
                    "payment_required": False,
                    "quote_required": True,
                },
                status=EventStatus.PENDING,
                attempts=0,
                available_at=datetime.now(UTC),
            )
        )
        # The reusable token is returned only at this creation boundary; only its hash is stored.
        setattr(booking, "guest_confirmation_token", guest_token)
        for answer in payload.answers:
            await self.repository.add(
                BookingAnswer(
                    booking_id=booking.id, question_id=answer.question_id, value=answer.value
                )
            )
        await self.session.commit()
        return booking
