from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "BREERO API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://breero:breero@postgres:5432/breero"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "development-only-change-me"
    jwt_refresh_secret: str = "development-only-change-me-too"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 30
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_enabled: bool = False
    scheduling_enabled: bool = True
    automatic_booking_enabled: bool = False
    automatic_provider_assignment_enabled: bool = False
    geocoding_api_key: str = ""
    geocoding_provider: str = "geoapify"
    geocoding_enabled: bool = False
    odoo_url: str = ""
    odoo_database: str = ""
    odoo_username: str = ""
    odoo_api_key: str = ""
    odoo_enabled: bool = False
    middleware_enabled: bool = False
    middleware_url: str = ""
    middleware_ca_file: str = ""
    middleware_client_cert_file: str = ""
    middleware_client_key_file: str = ""
    middleware_hmac_key_id: str = ""
    middleware_hmac_secret_file: str = ""
    middleware_service_identity: str = ""
    middleware_audience: str = ""
    middleware_tenant: str = ""
    middleware_scope: str = "breero.crm.events.submit"
    payout_api_key: str = ""
    metrics_enabled: bool = True
    payout_provider: str = ""
    payout_enabled: bool = False
    paid_leads_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    email_enabled: bool = False
    sms_provider: str = ""
    sms_api_key: str = ""
    sms_enabled: bool = False
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003"
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.app_env.lower() not in {"production", "staging"}:
            return self
        required = {
            "DATABASE_URL": self.database_url,
            "REDIS_URL": self.redis_url,
            "JWT_SECRET": self.jwt_secret,
            "JWT_REFRESH_SECRET": self.jwt_refresh_secret,
        }
        if self.stripe_enabled:
            required |= {
                "STRIPE_SECRET_KEY": self.stripe_secret_key,
                "STRIPE_WEBHOOK_SECRET": self.stripe_webhook_secret,
            }
        if self.app_env.lower() == "production" and (
            self.stripe_enabled or self.payout_enabled or self.paid_leads_enabled
        ):
            raise ValueError(
                "BREERO production launch is quote-only; payments, payouts, and paid leads "
                "must remain disabled"
            )
        if self.automatic_booking_enabled or self.automatic_provider_assignment_enabled:
            raise ValueError(
                "automatic booking and provider assignment require a separate production approval"
            )
        if self.geocoding_enabled:
            required["GEOCODING_API_KEY"] = self.geocoding_api_key
        if self.odoo_enabled:
            required["DIRECT_ODOO_PROHIBITED_USE_MIDDLEWARE"] = ""
        if self.middleware_enabled:
            required |= {
                "MIDDLEWARE_URL": self.middleware_url,
                "MIDDLEWARE_CA_FILE": self.middleware_ca_file,
                "MIDDLEWARE_CLIENT_CERT_FILE": self.middleware_client_cert_file,
                "MIDDLEWARE_CLIENT_KEY_FILE": self.middleware_client_key_file,
                "MIDDLEWARE_HMAC_KEY_ID": self.middleware_hmac_key_id,
                "MIDDLEWARE_HMAC_SECRET_FILE": self.middleware_hmac_secret_file,
                "MIDDLEWARE_SERVICE_IDENTITY": self.middleware_service_identity,
                "MIDDLEWARE_AUDIENCE": self.middleware_audience,
                "MIDDLEWARE_TENANT": self.middleware_tenant,
                "MIDDLEWARE_SCOPE": self.middleware_scope,
            }
        if self.email_enabled:
            required |= {
                "SMTP_HOST": self.smtp_host,
                "SMTP_USERNAME": self.smtp_username,
                "SMTP_PASSWORD": self.smtp_password,
                "SMTP_FROM_EMAIL": self.smtp_from_email,
            }
        if self.sms_enabled:
            required |= {"SMS_PROVIDER": self.sms_provider, "SMS_API_KEY": self.sms_api_key}
        if self.payout_enabled:
            required |= {
                "PAYOUT_PROVIDER": self.payout_provider,
                "PAYOUT_API_KEY": self.payout_api_key,
            }
        insecure = {
            "development-only-change-me",
            "development-only-change-me-too",
            "change-me",
            "change-me-too",
            "breero",
        }
        # ``breero`` is the canonical middleware tenant identifier, not a
        # credential. Keep rejecting it as a development/default value for
        # secrets and connection settings, while allowing the explicitly
        # named tenant field required by the signed middleware contract.
        missing = [
            name
            for name, value in required.items()
            if not value or (value in insecure and name != "MIDDLEWARE_TENANT")
        ]
        if len(self.jwt_secret) < 32 or len(self.jwt_refresh_secret) < 32:
            missing.append("JWT secrets (minimum 32 characters)")
        if self.jwt_secret == self.jwt_refresh_secret:
            missing.append("distinct JWT access and refresh secrets")
        if "breero:breero@" in self.database_url:
            missing.append("non-default DATABASE_URL credentials")
        if "*" in self.allowed_origins:
            missing.append("explicit CORS_ORIGINS")
        if not self.allowed_origins or all("localhost" in origin for origin in self.allowed_origins):
            missing.append("production CORS_ORIGINS")
        if missing:
            raise ValueError("unsafe production configuration: " + ", ".join(sorted(set(missing))))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
