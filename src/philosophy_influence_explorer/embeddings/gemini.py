"""Gemini-backed text embeddings."""

from __future__ import annotations

import math

import httpx

from philosophy_influence_explorer.embeddings.base import (
    EmbeddingModelInfo,
    EmbeddingProvider,
)


class GeminiEmbeddingProviderError(RuntimeError):
    """Raised when Gemini cannot produce a valid embedding."""


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Generate document and query embeddings through the Gemini API."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimensions: int,
        timeout_seconds: float,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GOOGLE_API_KEY is required for Gemini embeddings.")

        if model != "gemini-embedding-001":
            raise ValueError(
                "This provider currently supports gemini-embedding-001 only."
            )

        if not 128 <= dimensions <= 3072:
            raise ValueError("Gemini embedding dimensions must be 128..3072.")

        self._api_key = api_key.strip()
        self._model = model
        self._dimensions = dimensions
        self._timeout_seconds = timeout_seconds

    @property
    def model_info(self) -> EmbeddingModelInfo:
        """Return the configured vector contract."""
        return EmbeddingModelInfo(
            provider="gemini",
            model=self._model,
            dimensions=self._dimensions,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed documents in input order."""
        return [
            self._embed(text, task_type="RETRIEVAL_DOCUMENT")
            for text in texts
        ]

    def embed_query(self, text: str) -> list[float]:
        """Embed a search query."""
        return self._embed(text, task_type="RETRIEVAL_QUERY")

    def _embed(self, text: str, *, task_type: str) -> list[float]:
        if not text.strip():
            raise ValueError("Embedding text must not be blank.")

        model_resource = f"models/{self._model}"
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"{model_resource}:embedContent"
        )

        try:
            response = httpx.post(
                url,
                headers={"x-goog-api-key": self._api_key},
                json={
                    "model": model_resource,
                    "content": {"parts": [{"text": text}]},
                    "taskType": task_type,
                    "outputDimensionality": self._dimensions,
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise GeminiEmbeddingProviderError(
                "Gemini embedding request failed "
                f"(HTTP {error.response.status_code})."
            ) from None
        except httpx.HTTPError:
            raise GeminiEmbeddingProviderError(
                "Could not reach the Gemini embedding API."
            ) from None

        try:
            payload = response.json()
        except ValueError:
            raise GeminiEmbeddingProviderError(
                "Gemini returned invalid JSON."
            ) from None

        embedding = (
            payload.get("embedding")
            if isinstance(payload, dict)
            else None
        )
        values = (
            embedding.get("values")
            if isinstance(embedding, dict)
            else None
        )

        if not isinstance(values, list):
            raise GeminiEmbeddingProviderError(
                "Gemini response does not contain embedding.values."
            )

        if len(values) != self._dimensions:
            raise GeminiEmbeddingProviderError(
                "Gemini returned an unexpected dimension: "
                f"expected {self._dimensions}, got {len(values)}."
            )

        vector: list[float] = []

        for value in values:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise GeminiEmbeddingProviderError(
                    "Gemini returned a non-numeric embedding value."
                )

            try:
                number = float(value)
            except (OverflowError, ValueError):
                raise GeminiEmbeddingProviderError(
                    "Gemini returned an invalid numeric value."
                ) from None

            if not math.isfinite(number):
                raise GeminiEmbeddingProviderError(
                    "Gemini returned a non-finite embedding value."
                )

            vector.append(number)

        norm = math.hypot(*vector)
        if norm == 0 or not math.isfinite(norm):
            raise GeminiEmbeddingProviderError(
                "Gemini returned an invalid embedding norm."
            )

        return [value / norm for value in vector]
