from fastapi import APIRouter

from app.api.v1 import (
    addresses,
    auth,
    availability,
    bookings,
    customers,
    finance,
    integrations,
    jobs,
    operations,
    payments,
    services,
    vendors,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(availability.router, prefix="/availability", tags=["availability"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(customers.router, prefix="/customer", tags=["customer"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
