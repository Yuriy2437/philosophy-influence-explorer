"""Factory for selecting the configured embedding provider."""

from __future__ import annotations

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.embeddings.base import (
    EmbeddingProvider,
    NotConfiguredEmbeddingProvider,
)
from philosophy_influence_explorer.embeddings.gemini import (
    GeminiEmbeddingProvider,
)
from philosophy_influence_explorer.embeddings.ollama import (
    OllamaEmbeddingProvider,
)


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Create the embedding provider selected in application settings."""
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingProvider(
            base_url=settings.ollama_base_url,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            timeout_seconds=settings.embedding_timeout_seconds,
        )

    if settings.embedding_provider == "gemini":
        api_key = settings.google_api_key

        if api_key is None or not api_key.get_secret_value().strip():
            raise ValueError(
                "GOOGLE_API_KEY is required when EMBEDDING_PROVIDER=gemini."
            )

        return GeminiEmbeddingProvider(
            api_key=api_key.get_secret_value(),
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            timeout_seconds=settings.embedding_timeout_seconds,
        )

    if settings.embedding_provider == "not_configured":
        return NotConfiguredEmbeddingProvider()

    raise ValueError(
        "Unsupported embedding provider: "
        f"{settings.embedding_provider!r}."
    )
