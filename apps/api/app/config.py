from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "BREERO API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://breero:breero@postgres:5432/breero"
    redis_url: str = "redis://redis:6379/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
