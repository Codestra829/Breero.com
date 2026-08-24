"""Private operations surface for Odoo delivery. Network policy must keep /internal off public ingress."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import User, UserRole
from app.domains.common.outbox import EventStatus, IntegrationEvent
from app.domains.common.outbox_service import OutboxService

router = APIRouter(prefix="/internal/v1/integrations/odoo", tags=["private-odoo"])
authorized = require_roles(UserRole.operations, UserRole.finance, UserRole.admin)


def view(event: IntegrationEvent) -> dict:
    return {"event_id": event.id, "event_type": event.event_type, "status": event.status,
            "attempt": event.attempt_count, "next_retry_at": event.next_attempt_at,
            "odoo_model": event.external_model, "odoo_record_id": event.external_record_id,
            "error_code": event.last_error_code, "error_summary": event.last_error,
            "created_at": event.created_at, "updated_at": event.updated_at}


@router.get("/health")
async def health(session: AsyncSession = Depends(get_db), _: User = Depends(authorized)):
    rows = (await session.execute(select(IntegrationEvent.status, func.count()).where(
        IntegrationEvent.event_type.like("breero.%")).group_by(IntegrationEvent.status))).tuples()
    counts: dict[EventStatus, int] = {status: count for status, count in rows}
    return {"enabled": settings.odoo_enabled, "configured": bool(settings.odoo_url and settings.odoo_database and settings.odoo_username and settings.odoo_api_key),
            "delivery_counts": {str(key.value): value for key, value in counts.items()}}


@router.get("/deliveries/{event_id}")
async def delivery(event_id: uuid.UUID, session: AsyncSession = Depends(get_db), _: User = Depends(authorized)):
    event = await session.get(IntegrationEvent, event_id)
    if not event or not event.event_type.startswith("breero."):
        raise HTTPException(404, "Odoo delivery not found")
    return view(event)


@router.get("/failures")
async def failures(session: AsyncSession = Depends(get_db), _: User = Depends(authorized)):
    rows = (await session.scalars(select(IntegrationEvent).where(
        IntegrationEvent.event_type.like("breero.%"),
        IntegrationEvent.status.in_([EventStatus.FAILED, EventStatus.DEAD_LETTER, EventStatus.FAILED_TERMINAL])
    ).order_by(IntegrationEvent.updated_at.desc()).limit(200))).all()
    return [view(row) for row in rows]


@router.post("/deliveries/{event_id}/retry")
async def retry(event_id: uuid.UUID, session: AsyncSession = Depends(get_db), user: User = Depends(authorized)):
    try:
        return view(await OutboxService(session).retry(event_id, user.id))
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
