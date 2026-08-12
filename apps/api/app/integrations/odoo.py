from dataclasses import dataclass

import httpx

from app.config import settings


class OdooMapper:
    model: str

    def map(self, source: object) -> dict:
        raise NotImplementedError


def _value(source: object, name: str, default=None):
    return source.get(name, default) if isinstance(source, dict) else getattr(source, name, default)


class CustomerOdooMapper(OdooMapper):
    model = "res.partner"

    def map(self, customer: object) -> dict:
        return {"name": f"{_value(customer, 'first_name', '')} {_value(customer, 'last_name', '')}".strip(),
                "email": _value(customer, "email"), "phone": _value(customer, "phone"),
                "customer_rank": 1, "ref": str(_value(customer, "id"))}


class VendorOdooMapper(OdooMapper):
    model = "res.partner"

    def map(self, vendor: object) -> dict:
        return {"name": _value(vendor, "name"), "supplier_rank": 1,
                "ref": str(_value(vendor, "id"))}


class BookingOdooMapper(OdooMapper):
    """Default mapping to a sales order; deployments may configure a field-service model."""
    model = "sale.order"

    def map(self, booking: object) -> dict:
        return {"client_order_ref": _value(booking, "reference"),
                "x_breero_booking_id": str(_value(booking, "id")),
                "amount_total": float(_value(booking, "total_amount", 0))}


class JobOdooMapper(OdooMapper):
    """Maps to Odoo Field Service task when that module is enabled."""
    model = "project.task"

    def map(self, job: object) -> dict:
        return {"name": f"BREERO job {str(_value(job, 'id'))}",
                "x_breero_job_id": str(_value(job, "id")),
                "planned_date_begin": _value(job, "scheduled_start")}


class PaymentOdooMapper(OdooMapper):
    model = "account.payment"

    def map(self, payment: object) -> dict:
        return {"ref": str(_value(payment, "id")),
                "amount": _value(payment, "amount_minor", 0) / 100,
                "currency_code": _value(payment, "currency", "USD")}


class PayoutOdooMapper(OdooMapper):
    """Payouts become outbound supplier payments; vendor bills remain deployment policy."""
    model = "account.payment"

    def map(self, payout: object) -> dict:
        return {"ref": _value(payout, "reference"), "payment_type": "outbound",
                "partner_type": "supplier", "amount": _value(payout, "total_minor", 0) / 100,
                "currency_code": _value(payout, "currency", "USD")}


class PublicSubmissionOdooMapper(OdooMapper):
    """Public forms become CRM leads with a BREERO request ID as external reference."""

    model = "crm.lead"

    def map(self, source: object) -> dict:
        payload = _value(source, "payload", source)
        route = _value(source, "route", "CONTACT")
        route_title = str(route).replace("_", " ").title()
        detail_parts = [
            _value(payload, "service_description"),
            _value(payload, "message"),
            _value(payload, "notes"),
            _value(payload, "license_details"),
        ]
        location = ", ".join(
            str(value)
            for value in (
                _value(payload, "address_line1"),
                _value(payload, "city"),
                _value(payload, "state"),
                _value(payload, "postal_code"),
            )
            if value
        )
        attribution = ", ".join(
            f"{name}={value}"
            for name in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")
            if (value := _value(payload, name))
        )
        return {
            "name": f"BREERO {route_title}",
            "contact_name": _value(payload, "name") or _value(payload, "contact_name"),
            "partner_name": _value(payload, "business_name"),
            "email_from": _value(payload, "email"),
            "phone": _value(payload, "phone"),
            "description": "\n".join(
                part
                for part in (
                    *[str(value) for value in detail_parts if value],
                    f"Service: {_value(payload, 'service_slug')}" if _value(payload, "service_slug") else None,
                    f"Categories: {', '.join(_value(payload, 'service_categories', []))}" if _value(payload, "service_categories") else None,
                    f"Location: {location}" if location else None,
                    f"Requested timing: {_value(payload, 'requested_timing')}" if _value(payload, "requested_timing") else None,
                    f"Contact preference: {_value(payload, 'contact_preference')}" if _value(payload, "contact_preference") else None,
                    f"Attribution: {attribution}" if attribution else None,
                )
                if part
            ),
            "x_breero_request_id": str(_value(source, "submission_id")),
            "x_breero_form_route": route,
            "x_breero_source_url": _value(payload, "source_url"),
        }


MAPPERS = {
    "customer": CustomerOdooMapper(), "vendor": VendorOdooMapper(),
    "booking": BookingOdooMapper(), "job": JobOdooMapper(),
    "payment": PaymentOdooMapper(), "payout": PayoutOdooMapper(),
    "public_submission": PublicSubmissionOdooMapper(),
}


@dataclass(frozen=True)
class OdooResult:
    external_id: int


class OdooAdapter:
    """Small JSON-RPC boundary; domain services only publish outbox events."""

    async def execute(
        self, model: str, method: str, args: list, kwargs: dict | None = None
    ) -> object:
        if not all(
            [
                settings.odoo_url,
                settings.odoo_database,
                settings.odoo_username,
                settings.odoo_api_key,
            ]
        ):
            raise RuntimeError("Odoo integration is not configured")
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 1,
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    settings.odoo_database,
                    settings.odoo_username,
                    settings.odoo_api_key,
                    model,
                    method,
                    args,
                    kwargs or {},
                ],
            },
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{settings.odoo_url.rstrip('/')}/jsonrpc", json=payload)
            response.raise_for_status()
        body = response.json()
        if body.get("error"):
            raise RuntimeError(body["error"].get("message", "Odoo request failed"))
        return body.get("result")

    async def upsert(self, aggregate_type: str, source: object) -> object:
        mapper = MAPPERS.get(aggregate_type.lower())
        if not mapper:
            raise ValueError(f"No Odoo mapper for {aggregate_type}")
        values = mapper.map(source)
        if aggregate_type.lower() == "public_submission":
            external_id = values["x_breero_request_id"]
            existing = await self.execute(
                mapper.model,
                "search_read",
                [[("x_breero_request_id", "=", external_id)]],
                {"fields": ["id"], "limit": 1},
            )
            if (
                isinstance(existing, list)
                and existing
                and isinstance(existing[0], dict)
                and "id" in existing[0]
            ):
                record_id = existing[0]["id"]
                await self.execute(mapper.model, "write", [[record_id], values])
                return record_id
        return await self.execute(mapper.model, "create", [values])
