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
    geocoding_api_key: str = ""
    geocoding_provider: str = "geoapify"
    odoo_url: str = ""
    odoo_database: str = ""
    odoo_username: str = ""
    odoo_api_key: str = ""
    payout_api_key: str = ""
    metrics_enabled: bool = True
    payout_provider: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    sms_provider: str = ""
    sms_api_key: str = ""
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
            "STRIPE_SECRET_KEY": self.stripe_secret_key,
            "STRIPE_WEBHOOK_SECRET": self.stripe_webhook_secret,
            "GEOCODING_API_KEY": self.geocoding_api_key,
            "ODOO_URL": self.odoo_url,
            "ODOO_DATABASE": self.odoo_database,
            "ODOO_USERNAME": self.odoo_username,
            "ODOO_API_KEY": self.odoo_api_key,
            "SMTP_HOST": self.smtp_host,
            "SMTP_USERNAME": self.smtp_username,
            "SMTP_PASSWORD": self.smtp_password,
            "SMTP_FROM_EMAIL": self.smtp_from_email,
            "SMS_PROVIDER": self.sms_provider,
            "SMS_API_KEY": self.sms_api_key,
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
        missing = [name for name, value in required.items() if not value or value in insecure]
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
