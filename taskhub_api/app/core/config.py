from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TaskHub API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./taskhub.db"
    jwt_secret_key: SecretStr = SecretStr("development-only-change-this-secret-key-32bytes")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "taskhub-api"
    jwt_audience: str = "taskhub-client"
    jwt_expire_minutes: int = 60
    cors_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    api_key_enabled: bool = False
    api_key: SecretStr | None = None
    upload_dir: Path = Path("var/uploads")
    max_upload_bytes: int = 5 * 1024 * 1024
    external_timeout_seconds: float = 5.0
    auto_create_tables: bool = False

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.environment == "production":
            if self.jwt_secret_key.get_secret_value() == "development-only-change-this-secret-key-32bytes":
                raise ValueError("JWT_SECRET_KEY must be changed in production")
            if len(self.jwt_secret_key.get_secret_value()) < 32:
                raise ValueError("JWT_SECRET_KEY must contain at least 32 characters")
        if self.api_key_enabled and self.api_key is None:
            raise ValueError("API_KEY is required when API_KEY_ENABLED=true")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
