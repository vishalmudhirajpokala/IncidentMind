"""Typed application configuration.

All secrets and environment-specific values are read from the environment
(never hard-coded, never returned to the frontend). This module is the single
source of truth for configuration; nothing else in the app reads os.environ.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ app
    APP_NAME: str = "IncidentMind"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEMO_MODE: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # ------------------------------------------------------------- database
    DATABASE_URL: str = "sqlite:///./incidents.db"

    # ------------------------------------------------------------ hindsight
    HINDSIGHT_BASE_URL: str = ""
    HINDSIGHT_API_KEY: str = ""
    HINDSIGHT_BANK_ID: str = "incidentmind"
    # The Hindsight HTTP API is versioned and namespace scoped, e.g.
    # POST /v1/default/banks/{bank_id}/memories/recall
    HINDSIGHT_API_PREFIX: str = "/v1/default"
    HINDSIGHT_TIMEOUT_SECONDS: float = 20.0
    HINDSIGHT_RECALL_BUDGET: str = "mid"
    HINDSIGHT_RECALL_MAX_TOKENS: int = 4096
    HINDSIGHT_RETAIN_ASYNC: bool = False
    # auto = use Hindsight when configured, otherwise fall back to the local store
    MEMORY_PROVIDER: str = "auto"
    MEMORY_RECALL_LIMIT: int = 5

    # ------------------------------------------------------------------ llm
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL: str = "openai/gpt-oss-20b"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1200
    LLM_TIMEOUT_SECONDS: float = 45.0
    LLM_RETRIES: int = 1
    # auto = use Groq when configured, otherwise deterministic mock
    LLM_PROVIDER: str = "auto"

    # ------------------------------------------------------------------ web
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --------------------------------------------------------------- server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # ------------------------------------------------------------- helpers
    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def hindsight_configured(self) -> bool:
        return bool(self.HINDSIGHT_BASE_URL and self.HINDSIGHT_API_KEY)

    @property
    def llm_configured(self) -> bool:
        return bool(self.GROQ_API_KEY)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
