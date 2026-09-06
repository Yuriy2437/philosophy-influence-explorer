"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API and future AI infrastructure."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Philosophy Influence Explorer API"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "change-me-before-production"
    neo4j_database: str = "neo4j"

    llm_provider: str = "ollama"
    llm_model: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "philosophy-influence-explorer"

    @property
    def cors_origin_list(self) -> list[str]:
        """Return normalized CORS origins for FastAPI middleware."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Create and cache process-wide settings."""
    return Settings()
