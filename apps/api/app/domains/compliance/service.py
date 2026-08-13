import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.outbox import AuditLog

from .models import ConsentEvent, PrivacyRequest, PrivacyRequestStatus, Suppression
from .schemas import CommunicationPreferenceCreate, PrivacyRequestCreate


def digest(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


def is_revocation(message: str) -> bool:
    normalized = " ".join(message.upper().replace("-", " ").split())
    return normalized in {
        "STOP",
        "QUIT",
        "END",
        "REVOKE",
        "OPT OUT",
        "CANCEL",
        "UNSUBSCRIBE",
    } or any(
        phrase in normalized
        for phrase in ("STOP TEXTING", "DO NOT TEXT", "REMOVE ME", "NO MORE MESSAGES")
    )


class ComplianceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def suppress(
        self, destination_hash: str, channel: str, purpose: str, reason: str, source: str
    ):
        item = await self.session.scalar(
            select(Suppression).where(
                Suppression.destination_hash == destination_hash,
                Suppression.channel == channel,
                Suppression.purpose == purpose,
            )
        )
        if item:
            item.active = True
            item.reason = reason
            item.source = source
        else:
            self.session.add(
                Suppression(
                    destination_hash=destination_hash,
                    channel=channel,
                    purpose=purpose,
                    reason=reason,
                    source=source,
                )
            )

    async def privacy_request(
        self, data: PrivacyRequestCreate, source_ip: str, user_agent: str | None
    ):
        now = datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        item = PrivacyRequest(
            request_type=data.requestType,
            normalized_email=str(data.email).lower(),
            status=PrivacyRequestStatus.RECEIVED,
            verification_state="PENDING",
            receipt_token_hash=digest(token),
            jurisdiction=data.jurisdiction,
            due_at=now + timedelta(days=45),
            source_ip_hash=digest(source_ip),
            user_agent=user_agent,
            history=[{"at": now.isoformat(), "action": "received", "gpc": data.gpc}],
        )
        self.session.add(item)
        await self.session.flush()
        if data.requestType in {"opt_out_sale_sharing", "opt_out_targeted_ads"} or data.gpc:
            for purpose in ("SALE_SHARING", "TARGETED_ADVERTISING", "NONESSENTIAL_TRACKING"):
                await self.suppress(
                    digest(str(data.email)),
                    "ALL",
                    purpose,
                    "PRIVACY_OPT_OUT",
                    "GPC" if data.gpc else "PRIVACY_REQUEST",
                )
        self.session.add(
            AuditLog(
                actor_id=None,
                actor_type="consumer",
                action="privacy_request.received",
                resource_type="privacy_request",
                resource_id=item.id,
                metadata_json={"request_type": data.requestType, "gpc": data.gpc},
                created_at=now,
            )
        )
        await self.session.commit()
        return item, token

    async def preferences(
        self, data: CommunicationPreferenceCreate, source_ip: str, user_agent: str | None
    ):
        now = datetime.now(UTC)
        hashed = digest(data.destination)
        values = {
            "TRANSACTIONAL_EMAIL": data.transactionalEmail,
            "TRANSACTIONAL_SMS": data.transactionalSms,
            "MARKETING_EMAIL": data.marketingEmail,
            "MARKETING_SMS": data.marketingSms,
        }
        for purpose, granted in values.items():
            if ("EMAIL" in purpose) != ("@" in data.destination):
                continue
            self.session.add(
                ConsentEvent(
                    destination_hash=hashed,
                    customer_id=None,
                    purpose=purpose,
                    granted=granted,
                    occurred_at=now,
                    source_ip_hash=digest(source_ip),
                    user_agent=user_agent,
                    source_url=str(data.source_url),
                    disclosure_text=data.disclosure_text,
                    policy_versions=data.policy_versions,
                    evidence={"checkbox_state": granted, "brand": "BREERO"},
                )
            )
            if not granted:
                await self.suppress(
                    hashed,
                    "EMAIL" if "EMAIL" in purpose else "SMS",
                    purpose,
                    "PREFERENCE_WITHDRAWN",
                    "PREFERENCE_CENTER",
                )
        await self.session.commit()
        return not all(values.values())
