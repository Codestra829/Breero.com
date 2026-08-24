import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import User, UserRole
from app.domains.finance.models import EarningStatus
from app.domains.finance.repository import FinanceRepository
from app.domains.finance.schemas import (
    CompensationPlanCreate,
    CompensationPlanRead,
    EarningAdjustmentCreate,
    EarningRead,
    PayoutBatchCreate,
    PayoutBatchRead,
)
from app.domains.finance.service import FinanceService

router = APIRouter()


@router.post("/compensation-plans", response_model=CompensationPlanRead, status_code=201)
async def create_compensation_plan(
    payload: CompensationPlanCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.finance, UserRole.admin)),
):
    return await FinanceService(session).create_compensation_plan(payload, user.id)


@router.post("/earnings/{earning_id}/adjustments", status_code=201)
async def adjust_earning(
    earning_id: uuid.UUID,
    payload: EarningAdjustmentCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.finance, UserRole.admin)),
):
    return await FinanceService(session).adjust_earning(
        earning_id, payload.amount_minor, payload.adjustment_type, payload.reason,
        payload.idempotency_key, user.id,
    )


@router.get("/earnings", response_model=list[EarningRead])
async def list_earnings(
    vendor_id: uuid.UUID | None = None,
    status: EarningStatus | None = None,
    limit: int = Query(200, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.finance, UserRole.admin)),
):
    return await FinanceRepository(session).list_earnings(vendor_id, status, limit)


@router.post("/payout-batches", response_model=PayoutBatchRead, status_code=201)
async def create_batch(
    payload: PayoutBatchCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.finance, UserRole.admin)),
):
    return await FinanceService(session).create_batch(payload.currency, payload.vendor_id, _.id)


@router.post("/payout-batches/{batch_id}/approve", response_model=PayoutBatchRead)
async def approve_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.finance, UserRole.admin)),
):
    return await FinanceService(session).approve_batch(batch_id, user.id)


@router.post("/payout-batches/{batch_id}/submit", response_model=PayoutBatchRead)
async def submit_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.finance, UserRole.admin)),
):
    return await FinanceService(session).submit_batch(batch_id, user.id)
