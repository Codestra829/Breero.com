from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.booking.schemas import AddressValidateRequest, AddressValidationResponse
from app.domains.booking.service import AddressService

router = APIRouter()


@router.post("/validate", response_model=AddressValidationResponse)
async def validate_address(
    payload: AddressValidateRequest, session: AsyncSession = Depends(get_db)
) -> AddressValidationResponse:
    return await AddressService(session).validate(payload)
