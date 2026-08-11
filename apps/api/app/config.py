from functools import lru_cache

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
    odoo_url: str = ""
    odoo_database: str = ""
    odoo_username: str = ""
    odoo_api_key: str = ""
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003"
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
