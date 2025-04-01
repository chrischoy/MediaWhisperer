import os

from pydantic import field_validator
from pydantic_settings import BaseSettings


def parse_bool_env(value) -> bool:
    """Parse string to boolean, handling various formats."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if not value or value.lower() in ("false", "0", "no", "n", "f"):
            return False
    return True


# Get the absolute path to the API directory
API_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the absolute path to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(API_DIR))


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
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"

    # Storage settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(API_DIR, "uploads"))
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB

    # PDF processing settings
    PDF_TEMP_DIR: str = os.getenv("PDF_TEMP_DIR", os.path.join(API_DIR, "temp/pdf"))
    # For Google Gemini API
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    # For backward compatibility
    MARKER_PDF_ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Enable Vision LLM - set by validator
    USE_LLM: bool = False
    # Output format
    MARKER_OUTPUT_FORMAT: str = os.getenv("MARKER_OUTPUT_FORMAT", "markdown")

    @field_validator("USE_LLM", mode="before")
    @classmethod
    def validate_use_llm(cls, v):
        """Validate and parse USE_LLM from any format to boolean."""
        return parse_bool_env(v)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env


settings = Settings()
