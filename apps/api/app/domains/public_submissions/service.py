import hashlib
import json
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import DomainError
from app.domains.catalog.models import Service
from app.domains.common.outbox import EventStatus, IntegrationEvent

from .models import DownstreamStatus, PublicSubmission, SubmissionType
from .schemas import SubmissionAccepted, TrackingFields


class PublicSubmissionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def accept(
        self,
        submission_type: SubmissionType,
        data: TrackingFields,
        idempotency_key: str,
        source_ip: str,
    ) -> SubmissionAccepted:
        if data.company:
            raise DomainError("SUBMISSION_REJECTED", "Submission could not be accepted", 400)
        payload = data.model_dump(mode="json", exclude={"company"})
        request_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        existing = await self.session.scalar(
            select(PublicSubmission).where(
                PublicSubmission.submission_type == submission_type,
                PublicSubmission.idempotency_key == idempotency_key,
            )
        )
        if existing:
            if existing.request_hash != request_hash:
                raise DomainError("IDEMPOTENCY_CONFLICT", "Key already used for another request", 409)
            return SubmissionAccepted(
                request_id=existing.id, downstream_status=existing.downstream_status.value
            )
        if submission_type == SubmissionType.SERVICE_REQUEST:
            service_id = payload.get("service_id")
            service_slug = payload.get("service_slug")
            service = await self.session.scalar(
                select(Service).where(
                    Service.id == service_id if service_id else Service.slug == service_slug,
                    Service.is_active.is_(True),
                )
            )
            if not service:
                raise DomainError("SERVICE_NOT_FOUND", "Selected service is not available", 422)
            payload["service_id"] = str(service.id)
            payload["service_slug"] = service.slug
        email = str(payload["email"]).strip().lower()
        phone = re.sub(r"[^0-9+]", "", str(payload.get("phone") or "")) or None
        downstream = (
            DownstreamStatus.PENDING if settings.odoo_enabled else DownstreamStatus.PENDING_CONFIGURATION
        )
        submission = PublicSubmission(
            submission_type=submission_type,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            normalized_email=email,
            normalized_phone=phone,
            payload=payload,
            downstream_status=downstream,
            source_ip_hash=hashlib.sha256(source_ip.encode()).hexdigest(),
        )
        self.session.add(submission)
        await self.session.flush()
        self.session.add(
            IntegrationEvent(
                aggregate_type="public_submission",
                aggregate_id=submission.id,
                event_type={
                    SubmissionType.SERVICE_REQUEST: "breero.service_request.created",
                    SubmissionType.CONTACT: "breero.contact_request.created",
                    SubmissionType.PROVIDER_INTEREST: "breero.provider_interest.created",
                }[submission_type],
                aggregate_version=1,
                schema_version=1,
                idempotency_key=f"{submission_type.value.lower()}:{submission.id}:1",
                payload={
                    "submission_id": str(submission.id),
                    "route": submission_type.value,
                    "payload": payload,
                },
                status=(
                    EventStatus.PENDING
                    if settings.odoo_enabled
                    else EventStatus.PENDING_CONFIGURATION
                ),
                next_attempt_at=datetime.now(UTC),
                processed_at=None,
            )
        )
        await self.session.commit()
        return SubmissionAccepted(request_id=submission.id, downstream_status=downstream.value)
