from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AddressValidateRequest(BaseModel):
    address: str


@router.post("/validate")
async def validate_address(payload: AddressValidateRequest) -> dict:
    return {
        "serviceable": False,
        "formatted_address": payload.address,
        "address_id": None,
        "service_area_id": None,
        "legal_entity_code": None,
    }
