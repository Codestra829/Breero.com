import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import User, UserRole
from app.domains.dispatch.schemas import OfferDecision, OfferRead
from app.domains.dispatch.service import DispatchService
from app.domains.workforce.models import VendorStatus, Worker
from app.domains.workforce.repository import WorkforceRepository
from app.domains.workforce.schemas import VendorCreate, VendorRead, WorkerCreate, WorkerRead
from app.domains.workforce.service import WorkforceService

router = APIRouter()


async def _authorize_vendor(session: AsyncSession, user: User, vendor_id: uuid.UUID) -> None:
    from fastapi import HTTPException

    if user.role in {UserRole.admin, UserRole.operations}:
        return
    vendor = await WorkforceRepository(session).get_vendor(vendor_id)
    if not vendor or vendor.owner_user_id != user.id:
        raise HTTPException(403, "Account does not administer this vendor")


async def _worker_for_user(session: AsyncSession, user: User) -> Worker:
    from fastapi import HTTPException

    worker = await session.scalar(select(Worker).where(Worker.user_id == user.id))
    if not worker:
        raise HTTPException(403, "Account is not linked to a worker")
    return worker


@router.post("", response_model=VendorRead, status_code=201)
async def create_vendor(
    payload: VendorCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.operations)),
):
    return await WorkforceService(session).create_vendor(payload)


@router.get("", response_model=list[VendorRead])
async def list_vendors(
    status: VendorStatus | None = None,
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.operations)),
):
    return await WorkforceRepository(session).list_vendors(status, limit)


@router.post("/{vendor_id}/workers", response_model=WorkerRead, status_code=201)
async def create_worker(
    vendor_id: uuid.UUID,
    payload: WorkerCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.vendor_admin, UserRole.admin, UserRole.operations)),
):
    await _authorize_vendor(session, user, vendor_id)
    return await WorkforceService(session).add_worker(vendor_id, payload)


@router.get("/{vendor_id}/workers", response_model=list[WorkerRead])
async def list_workers(
    vendor_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.vendor_admin, UserRole.admin, UserRole.operations)),
):
    await _authorize_vendor(session, user, vendor_id)
    return await WorkforceRepository(session).list_workers(vendor_id)


@router.post("/{vendor_id}/offers/{offer_id}/decision", response_model=OfferRead)
async def decide_offer(
    vendor_id: uuid.UUID,
    offer_id: uuid.UUID,
    payload: OfferDecision,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.vendor_admin)),
):
    await _authorize_vendor(session, user, vendor_id)
    return await DispatchService(session).decide_offer(
        offer_id, vendor_id, payload.accept, payload.worker_id, user.id
    )
