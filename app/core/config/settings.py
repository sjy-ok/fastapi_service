from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from .database import DatabaseSettings
from .logging import LoggingSettings


class Settings(BaseSettings):
    app_name: str = "FastAPI Service"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    docs_enabled: bool = True
    database: DatabaseSettings
    logging: LoggingSettings = LoggingSettings()

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", env_nested_delimiter="__", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
