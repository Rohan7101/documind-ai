from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    APP_NAME: str = "DocuMind AI"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./data/documind.db"
    LOG_LEVEL: str = "INFO"
    MAX_UPLOAD_SIZE_MB: int = 10
    STORAGE_DIR: str = "storage/documents"

    # AI Configuration
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_MAX_INPUT_CHARS: int = 100_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


