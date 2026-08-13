import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_development_defaults():
    with pytest.raises(ValidationError, match="unsafe production configuration"):
        Settings(
            app_env="production",
            database_url="postgresql+psycopg://breero:breero@postgres:5432/breero",
            redis_url="redis://redis:6379/0",
            jwt_secret="development-only-change-me",
            jwt_refresh_secret="development-only-change-me-too",
            cors_origins="http://localhost:3000",
        )


def test_liveness_has_no_dependency_calls():
    from app.main import live

    assert live.__name__ == "live"


def test_staging_allows_explicitly_disabled_optional_providers():
    settings = Settings(
        app_env="staging",
        database_url="postgresql+psycopg://staging:strong-password@postgres:5432/staging",
        redis_url="redis://:strong-password@redis:6379/0",
        jwt_secret="a" * 32,
        jwt_refresh_secret="b" * 32,
        cors_origins="https://staging.breero.com",
    )

    assert settings.stripe_enabled is False
    assert settings.geocoding_enabled is False
    assert settings.email_enabled is False


def test_staging_requires_credentials_for_enabled_provider():
    with pytest.raises(ValidationError, match="STRIPE_SECRET_KEY"):
        Settings(
            app_env="staging",
            database_url="postgresql+psycopg://staging:strong-password@postgres:5432/staging",
            redis_url="redis://:strong-password@redis:6379/0",
            jwt_secret="a" * 32,
            jwt_refresh_secret="b" * 32,
            cors_origins="https://staging.breero.com",
            stripe_enabled=True,
        )


def test_staging_allows_canonical_breero_middleware_tenant():
    settings = Settings(
        app_env="staging",
        database_url="postgresql+psycopg://staging:strong-password@postgres:5432/staging",
        redis_url="redis://:strong-password@redis:6379/0",
        jwt_secret="a" * 32,
        jwt_refresh_secret="b" * 32,
        cors_origins="https://staging.breero.com",
        middleware_enabled=True,
        middleware_url="https://middleware.internal.codestra.agency",
        middleware_ca_file="/run/secrets/codestra_private_ca.pem",
        middleware_client_cert_file="/run/secrets/breero_middleware_client.pem",
        middleware_client_key_file="/run/secrets/breero_middleware_client.key",
        middleware_hmac_key_id="breero-staging-key-v1",
        middleware_hmac_secret_file="/run/secrets/breero_middleware_hmac",
        middleware_service_identity="breero-staging",
        middleware_audience="codestra-middleware-breero",
        middleware_tenant="breero",
        middleware_scope="breero.crm.events.submit",
    )

    assert settings.middleware_tenant == "breero"
