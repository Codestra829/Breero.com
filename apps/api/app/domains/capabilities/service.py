from app.config import Settings

from .schemas import PublicCapabilities


def public_capabilities(settings: Settings) -> PublicCapabilities:
    """Project effective behavior, not individual flags, into one public contract."""
    return PublicCapabilities(
        request_intake=True,
        instant_booking=(
            settings.scheduling_enabled
            and settings.automatic_booking_enabled
            and settings.automatic_confirmed_bookings
        ),
        online_payments=(
            settings.payments_enabled
            and settings.stripe_enabled
            and settings.online_checkout_enabled
        ),
        automatic_assignment=(
            settings.scheduling_enabled and settings.automatic_provider_assignment_enabled
        ),
        provider_self_service=settings.provider_self_service_enabled,
        marketplace_matching=settings.marketplace_matching_enabled,
        messaging=settings.marketplace_messaging_enabled,
        reviews=settings.marketplace_reviews_enabled,
    )
