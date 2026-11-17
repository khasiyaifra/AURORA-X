from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./aurora.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("jwt_secret")
    @classmethod
    def secret_is_configured(cls, value: str) -> str:
        if value == "change-me-in-production":
            return value
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
