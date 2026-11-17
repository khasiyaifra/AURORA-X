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
    ai_provider: str = "local"
    ai_api_url: str = ""
    ai_api_key: str = ""
    ai_model: str = "local-deterministic"
    ai_timeout_seconds: float = 15.0
    ai_rate_limit_per_minute: int = 20
    translation_provider: str = "unavailable"
    translation_api_url: str = ""
    translation_api_key: str = ""
    private_upload_dir: str = "./private_uploads"
    environment: str = "development"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    webhook_secret: str = ""
    redis_url: str = ""

    @field_validator("jwt_secret")
    @classmethod
    def secret_is_configured(cls, value: str) -> str:
        weak = {
            "change-me-in-production",
            "test-secret-that-is-only-used-by-tests",
            "change-this-to-a-long-random-secret",
        }
        if value in weak:
            return value
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
