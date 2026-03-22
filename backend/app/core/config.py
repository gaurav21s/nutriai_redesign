"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the NutriAI backend."""

    app_name: str = "NutriAI API"
    environment: Literal["local", "development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    cors_origins: str = "http://localhost:3000"

    log_level: str = "INFO"
    request_timeout_seconds: int = 45
    cache_ttl_seconds: int = 600

    max_upload_size_mb: int = 8
    allowed_image_types: str = "image/jpeg,image/jpg,image/png,image/webp"

    # Authentication (Clerk)
    auth_disabled: bool = False
    dev_user_id: str = "dev_user"
    clerk_issuer: str = ""
    clerk_jwt_public_key: str = ""
    clerk_audience: str = ""

    # AI provider keys
    google_api_key: str = ""
    together_api_key: str = ""
    groq_api_key: str = ""
    openai_api_key: str = ""
    allow_mock_ai_fallback: bool = True
    force_mock_ai_fallback: bool = False

    # Convex persistence
    enable_convex_persistence: bool = True
    convex_http_actions_url: str = ""
    convex_backend_secret: str = ""

    # Billing / Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # Non-secret business config
    affiliate_code: str = ""

    # Rate limit controls
    rate_limit_ai_per_minute: int = 10
    rate_limit_chat_per_minute: int = 30
    rate_limit_default_per_minute: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_cors_origins(self) -> list[str]:
        """Return CORS origins as a list."""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def get_allowed_image_types(self) -> list[str]:
        """Return allowed image types as a list."""
        return [item.strip() for item in self.allowed_image_types.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
