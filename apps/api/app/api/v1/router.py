from fastapi import APIRouter

from app.api.v1 import addresses, availability, bookings, services

api_router = APIRouter()
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(availability.router, prefix="/availability", tags=["availability"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
