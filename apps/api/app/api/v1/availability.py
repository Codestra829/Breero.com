from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AvailabilitySearchRequest(BaseModel):
    service_id: str
    address_id: str
    date_from: date
    date_to: date


@router.post("/search")
async def search_availability(payload: AvailabilitySearchRequest) -> dict:
    return {"dates": []}
