import secrets
from datetime import UTC, datetime, timedelta

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
                postal_code=payload.postal_code or "",
                country_code=payload.country_code.upper(),
                latitude=payload.latitude,
                longitude=payload.longitude,
                provider="provided",
            )
        match = await self.repository.service_area_at(resolved.longitude, resolved.latitude)
        if not match:
            return AddressValidationResponse(
                serviceable=False,
                formatted_address=resolved.formatted_address,
                address_id=None,
                service_area_id=None,
                legal_entity_code=None,
            )
        area, entity = match
        address = Address(
            formatted_address=resolved.formatted_address,
            line1=resolved.line1,
            city=resolved.city,
            postal_code=resolved.postal_code,
            country_code=resolved.country_code,
            service_area_id=area.id,
            geocoding_provider=resolved.provider,
            location=WKTElement(f"POINT({resolved.longitude} {resolved.latitude})", srid=4326),
        )
        await self.repository.add_address(address)
        await self.session.commit()
        return AddressValidationResponse(
            serviceable=True,
            formatted_address=address.formatted_address,
            address_id=address.id,
            service_area_id=area.id,
            legal_entity_code=entity.code,
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
                cursor = datetime.combine(current, rule.start_time, tzinfo=UTC)
                boundary = datetime.combine(current, rule.end_time, tzinfo=UTC)
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
        existing = await self.repository.booking_by_idempotency_key(idempotency_key)
        if existing:
            return existing
        if payload.window.start >= payload.window.end or payload.window.start <= datetime.now(UTC):
            raise DomainError("INVALID_BOOKING_WINDOW", "Booking window must be in the future", 422)
        address = await self.repository.address(payload.address_id)
        if not address or not address.service_area_id:
            raise DomainError(
                "ADDRESS_NOT_SERVICEABLE", "Address is outside an active service area", 422
            )
        slots = await self.availability.search(
            AvailabilitySearchRequest(
                service_id=payload.service_id,
                address_id=payload.address_id,
                date_from=payload.window.start.date(),
                date_to=payload.window.start.date(),
            )
        )
        if not any(
            slot.start == payload.window.start and slot.end == payload.window.end for slot in slots
        ):
            raise DomainError(
                "SLOT_UNAVAILABLE", "The selected time slot is no longer available", 409
            )
        entity = await self.repository.legal_entity_for_area(address.service_area_id)
        if not entity:
            raise DomainError("LEGAL_ENTITY_NOT_FOUND", "No legal entity serves this address", 422)
        service = await CatalogRepository(self.session).active_detail(str(payload.service_id))
        if not service:
            raise DomainError("SERVICE_NOT_FOUND", "Service is not available", 404)
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
        amount = service.base_price
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
            customer_id=customer.id,
            address_id=address.id,
            legal_entity_id=entity.id,
            service_id=payload.service_id,
            window_start=payload.window.start,
            window_end=payload.window.end,
            status=BookingStatus.PENDING_PAYMENT,
            pricing_snapshot={
                "service_id": str(payload.service_id),
                "service_name": service.name,
                "base_price": str(amount),
                "total": str(amount),
                "currency": entity.currency,
            },
            total_amount=amount,
            currency=entity.currency,
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        await self.repository.add(booking)
        for answer in payload.answers:
            await self.repository.add(
                BookingAnswer(
                    booking_id=booking.id, question_id=answer.question_id, value=answer.value
                )
            )
        await self.session.commit()
        return booking
