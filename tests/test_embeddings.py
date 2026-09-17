"""Tests for the embedding provider contract."""

from __future__ import annotations

import pytest

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.embeddings.base import (
    EmbeddingProviderNotConfiguredError,
    NotConfiguredEmbeddingProvider,
)
from philosophy_influence_explorer.embeddings.factory import (
    create_embedding_provider,
)
from philosophy_influence_explorer.embeddings.ollama import (
    OllamaEmbeddingProvider,
)


def test_factory_creates_ollama_provider() -> None:
    """The default configuration should select local Ollama embeddings."""
    settings = Settings(
        neo4j_password="test-password",
        embedding_provider="ollama",
        embedding_model="bge-m3:567m",
        embedding_dimensions=1024,
        embedding_timeout_seconds=60.0,
    )

    provider = create_embedding_provider(settings)

    assert isinstance(provider, OllamaEmbeddingProvider)
    assert provider.model_info.provider == "ollama"
    assert provider.model_info.model == "bge-m3:567m"
    assert provider.model_info.dimensions == 1024


def test_factory_creates_not_configured_provider() -> None:
    """The explicit placeholder remains available for disabled embeddings."""
    settings = Settings(
        neo4j_password="test-password",
        embedding_provider="not_configured",
    )

    provider = create_embedding_provider(settings)

    assert isinstance(provider, NotConfiguredEmbeddingProvider)


@pytest.mark.parametrize("method_name", ["embed_documents", "embed_query"])
def test_not_configured_provider_fails_clearly(method_name: str) -> None:
    """Embedding requests fail explicitly until a provider is configured."""
    provider = NotConfiguredEmbeddingProvider()

    with pytest.raises(EmbeddingProviderNotConfiguredError):
        if method_name == "embed_documents":
            provider.embed_documents(["Учёное незнание и абсолютное."])
        else:
            provider.embed_query("Что такое docta ignorantia?")
