from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.booking.schemas import AvailabilitySearchRequest, AvailabilitySlot
from app.domains.booking.service import AvailabilityService

router = APIRouter()


@router.post("/search", response_model=list[AvailabilitySlot])
async def search_availability(
    payload: AvailabilitySearchRequest, session: AsyncSession = Depends(get_db)
) -> list[AvailabilitySlot]:
    return await AvailabilityService(session).search(payload)
