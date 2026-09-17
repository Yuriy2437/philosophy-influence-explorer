"""Ollama-backed embedding provider."""

from __future__ import annotations

from typing import Any

import httpx

from philosophy_influence_explorer.embeddings.base import (
    EmbeddingModelInfo,
    EmbeddingProvider,
)


class OllamaEmbeddingProviderError(RuntimeError):
    """Raised when Ollama cannot produce valid embeddings."""


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Generate embeddings with Ollama's local /api/embed endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        dimensions: int,
        timeout_seconds: float,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dimensions = dimensions
        self._timeout_seconds = timeout_seconds

    @property
    def model_info(self) -> EmbeddingModelInfo:
        """Return metadata for the configured Ollama embedding model."""
        return EmbeddingModelInfo(
            provider="ollama",
            model=self._model,
            dimensions=self._dimensions,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate one validated embedding for every document text."""
        if not texts:
            return []

        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        """Generate one validated embedding for a query text."""
        embeddings = self._embed([text])

        if len(embeddings) != 1:
            raise OllamaEmbeddingProviderError(
                "Ollama returned an unexpected number of query embeddings."
            )

        return embeddings[0]

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        """Call Ollama and validate count, numeric values, and dimensions."""
        try:
            response = httpx.post(
                f"{self._base_url}/api/embed",
                json={
                    "model": self._model,
                    "input": inputs,
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise OllamaEmbeddingProviderError(
                f"Could not generate embeddings with Ollama: {error}"
            ) from error

        payload = self._parse_json(response)
        embeddings = payload.get("embeddings")

        if not isinstance(embeddings, list):
            raise OllamaEmbeddingProviderError(
                "Ollama response does not contain an 'embeddings' list."
            )

        if len(embeddings) != len(inputs):
            raise OllamaEmbeddingProviderError(
                "Ollama returned a different number of embeddings than inputs."
            )

        validated_embeddings: list[list[float]] = []

        for embedding in embeddings:
            if not isinstance(embedding, list):
                raise OllamaEmbeddingProviderError(
                    "Ollama returned an embedding that is not a list."
                )

            if len(embedding) != self._dimensions:
                raise OllamaEmbeddingProviderError(
                    "Ollama returned an embedding with an unexpected dimension: "
                    f"expected {self._dimensions}, got {len(embedding)}."
                )

            if any(
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                for value in embedding
            ):
                raise OllamaEmbeddingProviderError(
                    "Ollama returned an embedding containing a non-numeric value."
                )

            validated_embeddings.append(
                [float(value) for value in embedding]
            )

        return validated_embeddings

    @staticmethod
    def _parse_json(response: httpx.Response) -> dict[str, Any]:
        """Parse an Ollama response as a JSON object."""
        try:
            payload = response.json()
        except ValueError as error:
            raise OllamaEmbeddingProviderError(
                "Ollama returned an invalid JSON response."
            ) from error

        if not isinstance(payload, dict):
            raise OllamaEmbeddingProviderError(
                "Ollama returned a JSON response that is not an object."
            )

        return payload
