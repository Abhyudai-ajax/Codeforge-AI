"""
Configuration Management
Environment-based configuration using Pydantic Settings
"""

from typing import ClassVar, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings
    Configuration from environment variables with defaults.

    Values are loaded (in priority order) from:
      1. Actual environment variables
      2. ../.env  (project root when running from backend/)
      3. .env     (current working directory fallback)
    """

    # Application
    APP_NAME: str = "CodeForge AI"
    ENV: str = "development"
    DEBUG: bool = True
    VERSION: str = "0.1.0"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] | str = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",
    ]

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/codeforge_ai"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0

    # ---------------------------------------------------------------------------
    # JWT Authentication
    # ---------------------------------------------------------------------------
    # SECRET_KEY: keep this truly secret in production.
    # Generate a new one with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "change-this-in-production-use-a-random-64-char-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # AI Providers
    AI_PROVIDER: str = "openai"
    AI_TIMEOUT_SECONDS: int = 30
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"

    # Security and middleware
    TRUSTED_HOSTS: List[str] | str = ["localhost", "127.0.0.1", "testserver"]
    HTTPS_REDIRECT: bool = False
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    # Load from .env file — tries project root first, then CWD as fallback.
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    def _parse_cors_origins(cls, v):
        """Accept several formats for CORS_ORIGINS:

        - JSON list like ["http://...", ...]
        - Comma-separated string: http://a,https://b
        - Empty/None -> use defaults
        """
        if v is None:
            return v
        # if already a list, return as-is
        if isinstance(v, list):
            return v
        # If it's a string, try JSON first, then comma split
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            try:
                import json

                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            # fallback: comma-separated
            parts = [p.strip() for p in s.split(",") if p.strip()]
            return parts
        return v


# Global settings instance
settings = Settings()
