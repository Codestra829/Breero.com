from fastapi import APIRouter

from app.config import settings
from app.domains.capabilities.schemas import PublicCapabilities
from app.domains.capabilities.service import public_capabilities

router = APIRouter()


@router.get("/capabilities", response_model=PublicCapabilities)
async def capabilities() -> PublicCapabilities:
    return public_capabilities(settings)
