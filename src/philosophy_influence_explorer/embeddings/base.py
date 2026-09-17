"""Provider-neutral interfaces for text embeddings."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingModelInfo:
    """Describes a concrete embedding model and its vector contract."""

    provider: str
    model: str
    dimensions: int


class EmbeddingProvider(ABC):
    """Abstract interface for document and query embedding providers."""

    @property
    @abstractmethod
    def model_info(self) -> EmbeddingModelInfo:
        """Return provider/model metadata and embedding dimension."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Create one embedding vector per document text."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Create one embedding vector for a user query."""


class EmbeddingProviderNotConfiguredError(RuntimeError):
    """Raised when embedding generation is requested without a provider."""


class NotConfiguredEmbeddingProvider(EmbeddingProvider):
    """Explicit placeholder until an embedding provider is configured."""

    @property
    def model_info(self) -> EmbeddingModelInfo:
        """Return placeholder metadata without claiming a usable dimension."""
        return EmbeddingModelInfo(
            provider="not_configured",
            model="not_configured",
            dimensions=0,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Fail clearly instead of returning fabricated vectors."""
        raise EmbeddingProviderNotConfiguredError(
            "No embedding provider is configured. "
            "Configure an embedding provider before indexing passages."
        )

    def embed_query(self, text: str) -> list[float]:
        """Fail clearly instead of returning fabricated vectors."""
        raise EmbeddingProviderNotConfiguredError(
            "No embedding provider is configured. "
            "Configure an embedding provider before querying passages."
        )
