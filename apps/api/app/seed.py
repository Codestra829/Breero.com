import asyncio
import uuid
from datetime import time
from decimal import Decimal

from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from app.db.session import SessionLocal
from app.domains.booking.models import AvailabilityRule, LegalEntity, ServiceArea
from app.domains.catalog.models import QuestionType, Service, ServiceQuestion

ENTITY_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
AREA_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")
SERVICE_ID = uuid.UUID("00000000-0000-4000-8000-000000000003")


async def seed() -> None:
    async with SessionLocal() as session:
        if await session.scalar(select(LegalEntity.id).limit(1)):
            return
        entity = LegalEntity(
            id=ENTITY_ID,
            code="BREERO-DE",
            name="BREERO Deutschland GmbH",
            currency="EUR",
            active=True,
        )
        area = ServiceArea(
            id=AREA_ID,
            legal_entity_id=ENTITY_ID,
            name="Berlin launch area",
            active=True,
            boundary=WKTElement(
                "MULTIPOLYGON(((13.0 52.3,13.8 52.3,13.8 52.8,13.0 52.8,13.0 52.3)))", srid=4326
            ),
        )
        service = Service(
            id=SERVICE_ID,
            slug="home-repair-visit",
            name="Home repair visit",
            description="A qualified technician diagnoses and completes standard home repairs.",
            base_price=Decimal("89.00"),
            duration_minutes=120,
            is_active=True,
            sort_order=1,
        )
        question = ServiceQuestion(
            service_id=SERVICE_ID,
            key="problem_description",
            label="What needs fixing?",
            help_text="Describe the issue and anything the technician should know.",
            question_type=QuestionType.textarea,
            required=True,
            sort_order=1,
            is_active=True,
        )
        session.add_all([entity, area, service, question])
        await session.flush()
        for weekday in range(5):
            session.add(
                AvailabilityRule(
                    service_id=SERVICE_ID,
                    service_area_id=AREA_ID,
                    weekday=weekday,
                    start_time=time(8),
                    end_time=time(18),
                    slot_minutes=120,
                    capacity=4,
                )
            )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
