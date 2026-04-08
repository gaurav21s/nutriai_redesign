"""Application configuration using pydantic-settings."""

from __future__ import annotations

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
    operations_queue_ttl_seconds: int = 120
    operations_stream_poll_seconds: float = 0.25

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
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_chat_model: str = "openai/gpt-oss-20b:free"
    openrouter_fallback_models: str = ""
    openrouter_site_url: str = ""
    openrouter_app_name: str = "NutriAI"
    allow_mock_ai_fallback: bool = True
    force_mock_ai_fallback: bool = False
    agent_chat_provider: Literal["groq", "openrouter"] = "groq"

    # Convex persistence
    enable_convex_persistence: bool = True
    convex_http_actions_url: str = ""
    convex_backend_secret: str = ""
    require_shared_coordination_in_production: bool = True

    # Shared coordination / Redis
    redis_url: str = ""
    redis_key_prefix: str = "nutriai"

    # Billing / Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # Observability / analytics
    posthog_project_api_key: str = ""
    posthog_host: str = "https://us.i.posthog.com"
    axiom_api_token: str = ""
    axiom_domain: str = "https://us-east-1.aws.edge.axiom.co"
    axiom_backend_logs_dataset: str = "nutriai-backend-logs"
    axiom_frontend_events_dataset: str = "nutriai-frontend-events"
    axiom_traces_dataset: str = "nutriai-traces"
    otel_service_namespace: str = "nutriai"
    otel_trace_sample_rate: float = 1.0
    log_slow_request_ms: float = 1500.0
    log_success_sample_rate: float = 1.0
    log_vip_user_ids: str = ""

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

    def get_log_vip_user_ids(self) -> set[str]:
        """Return VIP user IDs that should bypass sampling."""
        return {item.strip() for item in self.log_vip_user_ids.split(",") if item.strip()}

    def get_axiom_base_url(self) -> str:
        """Return normalized Axiom ingest base URL."""
        return self.axiom_domain.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
