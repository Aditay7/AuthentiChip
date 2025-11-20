from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    APP_NAME: str = "AuthentiChip API"
    MONGO_URI: str = Field(validation_alias=AliasChoices("MONGO_URI", "mongodb_uri"))
    MONGO_DB: str = Field(validation_alias=AliasChoices("MONGO_DB", "mongodb_db"))

    SECRET_KEY: Optional[str] = Field(default=None, validation_alias=AliasChoices("SECRET_KEY", "secret_key"))
    JWT_ALGORITHM: str = Field(default="HS256", validation_alias=AliasChoices("JWT_ALGORITHM", "jwt_algorithm"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES", "access_token_expire_minutes")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, validation_alias=AliasChoices("REFRESH_TOKEN_EXPIRE_DAYS", "refresh_token_expire_days")
    )
    APP_ENV: str = Field(default="development", validation_alias=AliasChoices("APP_ENV", "app_env"))
    APP_HOST: str = Field(default="0.0.0.0", validation_alias=AliasChoices("APP_HOST", "app_host"))
    APP_PORT: int = Field(default=8000, validation_alias=AliasChoices("APP_PORT", "app_port"))
    UVICORN_WORKERS: int = Field(default=1, validation_alias=AliasChoices("UVICORN_WORKERS", "uvicorn_workers"))



@lru_cache()
def get_settings() -> Settings:
    return Settings()

