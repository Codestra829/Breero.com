"""Environment-aware, idempotent BREERO catalog seed.

Launch services are deliberately quote-required and non-bookable unless an operator
explicitly supplies BREERO_BOOKABLE_SERVICE_SLUGS after operational approval.
"""

import asyncio
import os

from sqlalchemy import select

from app.config import settings
from app.db.session import SessionLocal
from app.domains.catalog.models import Service

LAUNCH_SERVICES = (
    ("plumbing", "Plumbing", "Plumbing repair and installation requests."),
    ("electrical", "Electrical", "Electrical repair and installation requests."),
    ("handyman", "Handyman", "General home repair and maintenance requests."),
    ("heating", "Heating", "Heating system service requests."),
    ("cooling", "Cooling", "Cooling and air-conditioning service requests."),
    ("appliance-repair", "Appliance repair", "Household appliance repair requests."),
    ("cleaning", "Cleaning", "Residential cleaning service requests."),
    ("locksmith", "Locksmith", "Lock and entry service requests."),
    ("painting", "Painting", "Interior and exterior painting requests."),
    ("carpentry", "Carpentry", "Carpentry and woodwork requests."),
    ("moving-help", "Moving help", "Loading, unloading, and moving-help requests."),
    ("home-maintenance", "Home maintenance", "Recurring and seasonal maintenance requests."),
)

KNOWN_CERTIFICATION_PREFIXES = ("e2e-service-", "test-", "fixture-", "certification-")


async def seed() -> None:
    environment = settings.app_env.lower()
    if environment not in {"staging", "production"}:
        raise RuntimeError("Launch catalog seed requires APP_ENV=staging or production")
    approved_bookable = {
        slug.strip()
        for slug in os.getenv("BREERO_BOOKABLE_SERVICE_SLUGS", "").split(",")
        if slug.strip()
    }
    unknown = approved_bookable - {row[0] for row in LAUNCH_SERVICES}
    if unknown:
        raise RuntimeError(f"Unknown approved bookable service slugs: {sorted(unknown)}")

    async with SessionLocal() as session:
        rows = list((await session.scalars(select(Service))).all())
        launch_slugs = {row[0] for row in LAUNCH_SERVICES}
        for service in rows:
            certification = service.slug.startswith(KNOWN_CERTIFICATION_PREFIXES)
            legacy_berlin = service.slug == "home-repair-visit"
            if certification or legacy_berlin:
                service.is_active = False
                service.is_bookable = False

        by_slug = {row.slug: row for row in rows}
        for order, (slug, name, description) in enumerate(LAUNCH_SERVICES, start=1):
            launch_service = by_slug.get(slug)
            if launch_service is None:
                launch_service = Service(slug=slug)
                session.add(launch_service)
            launch_service.name = name
            launch_service.description = description
            launch_service.category = "home-services"
            launch_service.base_price = None
            launch_service.pricing_model = "quote_required"
            launch_service.duration_minutes = None
            launch_service.is_active = True
            launch_service.is_bookable = slug in approved_bookable
            launch_service.sort_order = order

        # Never silently publish an unknown service in launch environments.
        for service in rows:
            if service.slug not in launch_slugs:
                service.is_active = False
                service.is_bookable = False
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
