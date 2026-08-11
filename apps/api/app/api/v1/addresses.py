from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.domains.booking.schemas import AddressValidateRequest, AddressValidationResponse
from app.domains.booking.service import AddressService

router = APIRouter()


@router.post("/validate", response_model=AddressValidationResponse)
async def validate_address(
    payload: AddressValidateRequest,
    session: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit("address-validation", 30, 60)),
) -> AddressValidationResponse:
    return await AddressService(session).validate(payload)
