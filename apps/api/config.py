import os

from pydantic import field_validator
from pydantic_settings import BaseSettings


def parse_bool_env(value) -> bool:
    """Parse string to boolean, handling various formats."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        # Check for empty string first
        if not value or value.lower() in ("false", "0", "no", "n", "f"):
            return False
    # Consider any non-false value as True, or be stricter if needed
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
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "your-super-secret-and-long-random-string"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mediawhisperer.db")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_ECHO: bool = False  # Default set here, validator runs before

    # Storage settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(API_DIR, "uploads"))
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB

    # PDF processing settings
    PDF_TEMP_DIR: str = os.getenv("PDF_TEMP_DIR", os.path.join(API_DIR, "temp/pdf"))
    # For Google Gemini API
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    # For backward compatibility
    MARKER_PDF_ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Enable Vision LLM
    USE_LLM: bool = False  # Default set here, validator runs before
    # Output format
    MARKER_OUTPUT_FORMAT: str = os.getenv("MARKER_OUTPUT_FORMAT", "markdown")

    @field_validator("DEBUG", "DATABASE_ECHO", "USE_LLM", mode="before")
    @classmethod
    def parse_env_booleans(cls, v):
        """Validate and parse boolean fields from env vars before standard validation."""
        # Get value from env var if not directly passed
        # Note: BaseSettings handles loading from os.getenv implicitly for declared fields
        # We just need to parse the value it finds.
        return parse_bool_env(v)

    # Ensure integer fields handle potential env var strings
    @field_validator(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "DATABASE_POOL_SIZE",
        "DATABASE_MAX_OVERFLOW",
        "MAX_UPLOAD_SIZE",
        mode="before",
    )
    @classmethod
    def parse_env_integers(cls, v):
        """Parse integer fields from env vars before standard validation."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                # Handle error or raise a specific validation error
                raise ValueError(
                    f"Invalid integer format for environment variable: {v}"
                )
        return v  # Return as is if already an int or other type

    class Config:
        # Load environment variables from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Changed from ignore to allow, explicitly define fields above


settings = Settings()
