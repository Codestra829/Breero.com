from dataclasses import dataclass

from .models import CompensationMethod, VendorCompensationPlan, VendorServiceCompensation


@dataclass(frozen=True)
class CalculatedCompensation:
    amount_minor: int
    rule: dict


def calculate_compensation(
    plan: VendorCompensationPlan,
    gross_minor: int,
    service_rate: VendorServiceCompensation | None = None,
) -> CalculatedCompensation:
    if gross_minor < 0:
        raise ValueError("gross_minor cannot be negative")
    if plan.method == CompensationMethod.FIXED_MINOR:
        if plan.fixed_minor is None or plan.fixed_minor < 0:
            raise ValueError("fixed compensation is not configured")
        return CalculatedCompensation(plan.fixed_minor, {"fixed_minor": plan.fixed_minor})
    if plan.method == CompensationMethod.PERCENTAGE:
        if plan.percentage_bps is None or not 0 <= plan.percentage_bps <= 10_000:
            raise ValueError("percentage_bps must be between 0 and 10000")
        amount = gross_minor * plan.percentage_bps // 10_000
        return CalculatedCompensation(amount, {"percentage_bps": plan.percentage_bps})
    if not service_rate or service_rate.rate_minor < 0:
        raise ValueError("service compensation rate is not configured")
    return CalculatedCompensation(
        service_rate.rate_minor,
        {"service_rate_minor": service_rate.rate_minor, "service_id": str(service_rate.service_id)},
    )
