"""
Configuration management for the Document Search & Retrieval System.
Loads and validates environment variables using Pydantic.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    vision_agent_api_key: str = Field(..., alias="VISION_AGENT_API_KEY")
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")

    # Elasticsearch
    elasticsearch_url: str = Field(default="http://localhost:9200", alias="ELASTICSEARCH_URL")
    elasticsearch_user: str = Field(default="elastic", alias="ELASTICSEARCH_USER")
    elasticsearch_password: str = Field(..., alias="ELASTICSEARCH_PASSWORD")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # Application
    api_key: str = Field(..., alias="API_KEY")
    pdf_storage_path: str = Field(default="./data/pdfs", alias="PDF_STORAGE_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_file_size_mb: int = Field(default=100, alias="MAX_FILE_SIZE_MB")

    # Optional settings
    environment: str = Field(default="development", alias="ENVIRONMENT")
    cors_origins: list[str] = Field(default=["*"], alias="CORS_ORIGINS")

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v_upper

    @validator("max_file_size_mb")
    def validate_max_file_size(cls, v: int) -> int:
        """Validate max file size is reasonable (1-500 MB)."""
        if v < 1 or v > 500:
            raise ValueError("MAX_FILE_SIZE_MB must be between 1 and 500")
        return v

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance (singleton pattern).

    Returns:
        Settings: The application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Export settings for easy import
settings = get_settings()
