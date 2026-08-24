import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.compliance.models import PrivacyRequest
from app.domains.compliance.schemas import (
    CommunicationPreferenceCreate,
    PreferenceAccepted,
    PrivacyRequestAccepted,
    PrivacyRequestCreate,
    PrivacyRequestView,
    SmsRevocation,
)
from app.domains.compliance.service import ComplianceService, digest, is_revocation

router = APIRouter()


@router.post("/privacy-requests", response_model=PrivacyRequestAccepted, status_code=202)
async def create_privacy_request(
    data: PrivacyRequestCreate, request: Request, session: AsyncSession = Depends(get_db)
):
    item, token = await ComplianceService(session).privacy_request(
        data,
        request.client.host if request.client else "unknown",
        request.headers.get("user-agent"),
    )
    return PrivacyRequestAccepted(
        request_id=item.id,
        status=item.status.value,
        receipt_token=token,
        due_at=item.due_at.isoformat(),
    )


@router.get("/privacy-requests/{request_id}", response_model=PrivacyRequestView)
async def privacy_request_status(
    request_id: uuid.UUID,
    authorization: str = Header(alias="Authorization"),
    session: AsyncSession = Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Receipt token required")
    item = await session.get(PrivacyRequest, request_id)
    if not item or item.receipt_token_hash != digest(authorization.removeprefix("Bearer ")):
        raise HTTPException(403, "Invalid receipt token")
    return PrivacyRequestView(
        request_id=item.id,
        request_type=item.request_type,
        status=item.status.value,
        verification_state=item.verification_state,
        due_at=item.due_at.isoformat(),
        completed_at=item.completed_at.isoformat() if item.completed_at else None,
    )


@router.post("/communications/preferences", response_model=PreferenceAccepted, status_code=202)
async def preferences(
    data: CommunicationPreferenceCreate, request: Request, session: AsyncSession = Depends(get_db)
):
    active = await ComplianceService(session).preferences(
        data,
        request.client.host if request.client else "unknown",
        request.headers.get("user-agent"),
    )
    return PreferenceAccepted(suppression_active=active)


@router.post("/communications/sms-revocations", status_code=204)
async def sms_revocation(data: SmsRevocation, session: AsyncSession = Depends(get_db)):
    if not is_revocation(data.message):
        raise HTTPException(422, "Message is not a recognized revocation")
    await ComplianceService(session).suppress(
        digest(data.phone), "SMS", "MARKETING_SMS", "RECIPIENT_REVOCATION", "SMS_INBOUND"
    )
    await session.commit()
