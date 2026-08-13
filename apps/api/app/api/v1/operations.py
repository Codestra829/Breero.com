import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import User, UserRole
from app.domains.booking.models import ProviderServiceCoverage, ProviderWorkingHours
from app.domains.catalog.models import Service
from app.domains.common.outbox import AuditLog
from app.domains.dispatch.schemas import AssignmentRead, ManualAssignment, OfferRead
from app.domains.dispatch.service import DispatchService
from app.domains.public_submissions.models import PublicSubmission
from app.domains.public_submissions.schemas import DispatcherAuditEntry, DispatcherQueueItem
from app.domains.workforce.repository import WorkforceRepository
from app.domains.workforce.schemas import BookingCoverageWrite, VendorRead, VendorStatusUpdate

router = APIRouter()


@router.get("/dispatcher/queue", response_model=list[DispatcherQueueItem])
async def dispatcher_queue(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
) -> list[DispatcherQueueItem]:
    submissions = list(
        (
            await session.scalars(
                select(PublicSubmission).order_by(PublicSubmission.created_at.asc()).limit(500)
            )
        ).all()
    )
    submission_ids = [item.id for item in submissions]
    audits = (
        list(
            (
                await session.scalars(
                    select(AuditLog)
                    .where(
                        AuditLog.resource_type == "public_submission",
                        AuditLog.resource_id.in_(submission_ids),
                    )
                    .order_by(AuditLog.created_at.asc())
                )
            ).all()
        )
        if submission_ids
        else []
    )
    audits_by_request: dict[uuid.UUID, list[DispatcherAuditEntry]] = {}
    for audit in audits:
        audits_by_request.setdefault(audit.resource_id, []).append(
            DispatcherAuditEntry(
                action=audit.action,
                actor_id=audit.actor_id,
                metadata=audit.metadata_json,
                created_at=audit.created_at,
            )
        )

    now = datetime.now(UTC)
    result: list[DispatcherQueueItem] = []
    for submission in submissions:
        payload = submission.payload
        created_at = submission.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        manual_state = payload.get("manual_dispatch_state")
        provider_assigned = payload.get("provider_assigned") is True
        contact_attempts = payload.get("contact_attempts") or []
        result.append(
            DispatcherQueueItem(
                request_id=submission.id,
                submission_type=submission.submission_type.value,
                created_at=created_at,
                request_age_seconds=max(0, int((now - created_at).total_seconds())),
                required_follow_up=(
                    submission.submission_type.value != "SERVICE_REQUEST"
                    or manual_state == "PENDING_MANUAL_DISPATCH"
                    or not provider_assigned
                ),
                customer_timezone=payload.get("customer_timezone"),
                address_verification_state=payload.get("geoapify_verification_state"),
                manual_dispatch_state=manual_state,
                provider_assigned=provider_assigned,
                contact_attempts=contact_attempts,
                downstream_status=submission.downstream_status.value,
                payload=payload,
                audit_history=audits_by_request.get(submission.id, []),
            )
        )
    return result


@router.put("/workers/{worker_id}/booking-coverage", status_code=204)
async def replace_booking_coverage(
    worker_id: uuid.UUID,
    payload: BookingCoverageWrite,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    worker = await WorkforceRepository(session).get_worker(worker_id)
    if not worker:
        from fastapi import HTTPException
        raise HTTPException(404, "Worker not found")
    existing_services = set((await session.scalars(
        select(Service.id).where(Service.id.in_(payload.service_ids), Service.is_active.is_(True))
    )).all())
    if existing_services != set(payload.service_ids):
        from fastapi import HTTPException
        raise HTTPException(422, "Coverage contains an unavailable service")
    await session.execute(delete(ProviderServiceCoverage).where(ProviderServiceCoverage.worker_id == worker_id))
    await session.execute(delete(ProviderWorkingHours).where(ProviderWorkingHours.worker_id == worker_id))
    for service_id in payload.service_ids:
        for postal_code in sorted(set(payload.postal_codes)):
            session.add(ProviderServiceCoverage(
                worker_id=worker_id, service_id=service_id, postal_code=postal_code
            ))
    for weekday in sorted(set(payload.weekdays)):
        session.add(ProviderWorkingHours(
            worker_id=worker_id, weekday=weekday, start_time=payload.start_time,
            end_time=payload.end_time, capacity=payload.capacity,
        ))
    await session.commit()


@router.post("/jobs/{job_id}/match", response_model=list[OfferRead])
async def match_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await DispatchService(session).match(job_id, user.id)


@router.post("/jobs/{job_id}/assign", response_model=AssignmentRead, status_code=201)
async def assign_job(
    job_id: uuid.UUID,
    payload: ManualAssignment,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await DispatchService(session).manual_assign(
        job_id, payload.vendor_id, payload.worker_id, user.id, payload.reason
    )


@router.patch("/vendors/{vendor_id}/status", response_model=VendorRead)
async def set_vendor_status(
    vendor_id: uuid.UUID,
    payload: VendorStatusUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    from fastapi import HTTPException

    vendor = await WorkforceRepository(session).get_vendor(vendor_id, lock=True)
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    vendor.status = payload.status
    await session.commit()
    await session.refresh(vendor)
    return vendor
