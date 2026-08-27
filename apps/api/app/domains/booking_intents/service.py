import secrets
import uuid
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.booking.models import Address
from app.domains.catalog.models import Service
from app.domains.common.clock import Clock, SystemClock
from app.domains.common.outbox import AuditLog

from .models import BookingIntent, BookingIntentStatus
from .repository import BookingIntentRepository
from .schemas import BookingIntentCreate, BookingIntentUpdate

BOOKING_INTENT_TTL = timedelta(minutes=120)
EDITABLE_STATUSES = frozenset(
    {
        BookingIntentStatus.DRAFT,
        BookingIntentStatus.ADDRESS_VALIDATED,
        BookingIntentStatus.COVERAGE_CONFIRMED,
        BookingIntentStatus.AVAILABILITY_FOUND,
    }
)


class BookingIntentService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        clock: Clock | None = None,
        ttl: timedelta = BOOKING_INTENT_TTL,
    ) -> None:
        self.session = session
        self.clock = clock or SystemClock()
        self.ttl = ttl
        self.repository = BookingIntentRepository(session)

    async def create(
        self,
        command: BookingIntentCreate,
        anonymous_session_id: uuid.UUID,
    ) -> BookingIntent:
        await self._active_service(command.service_id)
        now = self.clock.now()
        intent = BookingIntent(
            public_reference=self._reference(),
            anonymous_session_id=anonymous_session_id,
            service_id=command.service_id,
            status=BookingIntentStatus.DRAFT,
            expires_at=now + self.ttl,
            version=1,
        )
        await self.repository.add(intent)
        self._audit(
            intent,
            "booking_intent.create",
            {"service_id": str(intent.service_id)},
        )
        await self.session.commit()
        await self.session.refresh(intent)
        return intent

    async def get(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
    ) -> BookingIntent:
        intent = await self._owned(intent_id, anonymous_session_id)
        await self._reject_expired(intent)
        return intent

    async def update(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
        command: BookingIntentUpdate,
        *,
        expected_version: int,
    ) -> BookingIntent:
        intent = await self._owned(intent_id, anonymous_session_id, lock=True)
        await self._reject_expired(intent)
        self._require_version(intent, expected_version)
        if intent.status not in EDITABLE_STATUSES:
            raise DomainError(
                "BOOKING_INTENT_NOT_EDITABLE",
                "Booking intent cannot be changed in its current state.",
                409,
            )

        values = command.model_dump(exclude_unset=True, exclude={"clear_selected_slot"})
        if "service_id" in values:
            service_id = values["service_id"]
            if service_id is None:
                raise DomainError(
                    "SERVICE_REQUIRED",
                    "A service is required for the booking intent.",
                    422,
                )
            await self._active_service(service_id)
            if service_id != intent.service_id:
                intent.service_id = service_id
                intent.address_id = None
                intent.timezone_id = None
                intent.requested_date = None
                intent.selected_slot = None
                intent.status = BookingIntentStatus.DRAFT

        if "address_id" in values:
            address_id = values["address_id"]
            if address_id is not None and await self.session.get(Address, address_id) is None:
                raise DomainError(
                    "ADDRESS_NOT_FOUND",
                    "Validated address was not found.",
                    422,
                )
            intent.address_id = address_id
            intent.selected_slot = None
            intent.status = (
                BookingIntentStatus.ADDRESS_VALIDATED
                if address_id is not None
                else BookingIntentStatus.DRAFT
            )

        if "timezone_id" in values:
            timezone_id = values["timezone_id"]
            if timezone_id is not None:
                self._timezone(timezone_id)
            intent.timezone_id = timezone_id
            intent.selected_slot = None

        if "requested_date" in values:
            requested_date = values["requested_date"]
            if requested_date is not None:
                zone = self._timezone(intent.timezone_id) if intent.timezone_id else ZoneInfo("UTC")
                if requested_date < self.clock.now().astimezone(zone).date():
                    raise DomainError(
                        "REQUESTED_DATE_IN_PAST",
                        "Requested service date cannot be in the past.",
                        422,
                    )
            intent.requested_date = requested_date
            intent.selected_slot = None

        if command.clear_selected_slot:
            intent.selected_slot = None
            if intent.address_id is not None:
                intent.status = BookingIntentStatus.ADDRESS_VALIDATED
            else:
                intent.status = BookingIntentStatus.DRAFT

        selected_slot = command.selected_slot
        if "selected_slot" in values and selected_slot is not None:
            if not intent.address_id or not intent.timezone_id or not intent.requested_date:
                raise DomainError(
                    "BOOKING_INTENT_INCOMPLETE",
                    "Address, timezone and requested date are required before selecting a slot.",
                    422,
                )
            intent.selected_slot = selected_slot.model_dump()
            intent.status = BookingIntentStatus.AVAILABILITY_FOUND

        intent.version += 1
        self._audit(
            intent,
            "booking_intent.update",
            {"status": intent.status.value, "version": intent.version},
        )
        await self.session.commit()
        await self.session.refresh(intent)
        return intent

    async def abandon(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
        *,
        expected_version: int,
    ) -> None:
        intent = await self._owned(intent_id, anonymous_session_id, lock=True)
        self._require_version(intent, expected_version)
        if intent.status == BookingIntentStatus.SUBMITTED:
            raise DomainError(
                "BOOKING_INTENT_ALREADY_SUBMITTED",
                "Submitted booking intents cannot be abandoned.",
                409,
            )
        if intent.status != BookingIntentStatus.EXPIRED:
            intent.status = BookingIntentStatus.EXPIRED
            intent.selected_slot = None
            intent.version += 1
            self._audit(
                intent,
                "booking_intent.abandon",
                {"version": intent.version},
            )
            await self.session.commit()

    async def _active_service(self, service_id: uuid.UUID) -> Service:
        service = await self.session.get(Service, service_id)
        if not service or not service.is_active:
            raise DomainError("SERVICE_NOT_FOUND", "Service not found.", 404)
        return service

    async def _owned(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
        *,
        lock: bool = False,
    ) -> BookingIntent:
        intent = await self.repository.owned(
            intent_id,
            anonymous_session_id,
            lock=lock,
        )
        if not intent:
            raise DomainError("BOOKING_INTENT_NOT_FOUND", "Booking intent not found.", 404)
        return intent

    async def _reject_expired(self, intent: BookingIntent) -> None:
        if (
            intent.status not in {BookingIntentStatus.EXPIRED, BookingIntentStatus.SUBMITTED}
            and intent.expires_at <= self.clock.now()
        ):
            intent.status = BookingIntentStatus.EXPIRED
            intent.selected_slot = None
            intent.version += 1
            self._audit(
                intent,
                "booking_intent.expire",
                {"version": intent.version},
            )
            await self.session.commit()
        if intent.status == BookingIntentStatus.EXPIRED:
            raise DomainError(
                "BOOKING_INTENT_EXPIRED",
                "Booking intent has expired.",
                410,
            )

    @staticmethod
    def _require_version(intent: BookingIntent, expected_version: int) -> None:
        if intent.version != expected_version:
            raise DomainError(
                "BOOKING_INTENT_VERSION_CONFLICT",
                "Booking intent was changed by another request.",
                409,
                fields={"current_version": intent.version},
            )

    @staticmethod
    def _timezone(timezone_id: str | None) -> ZoneInfo:
        if not timezone_id:
            raise DomainError(
                "TIMEZONE_REQUIRED",
                "Service-address timezone is required.",
                422,
            )
        try:
            return ZoneInfo(timezone_id)
        except ZoneInfoNotFoundError as exc:
            raise DomainError(
                "TIMEZONE_INVALID",
                "Service-address timezone is invalid.",
                422,
            ) from exc

    @staticmethod
    def _reference() -> str:
        return "BI-" + secrets.token_hex(8).upper()

    def _audit(self, intent: BookingIntent, action: str, metadata: dict) -> None:
        self.session.add(
            AuditLog(
                actor_id=None,
                actor_type="anonymous_session",
                action=action,
                resource_type="booking_intent",
                resource_id=intent.id,
                metadata_json={
                    "public_reference": intent.public_reference,
                    "anonymous_session_id": str(intent.anonymous_session_id),
                    **metadata,
                },
                created_at=self.clock.now(),
            )
        )
