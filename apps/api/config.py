import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Base settings
    APP_NAME: str = "MediaWhisperer API"
    DEBUG: bool = True

    # API settings
    API_PREFIX: str = "/api"

    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mediawhisperer.db")

    # Storage settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB

    # PDF processing settings
    PDF_TEMP_DIR: str = os.getenv("PDF_TEMP_DIR", "./temp/pdf")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
