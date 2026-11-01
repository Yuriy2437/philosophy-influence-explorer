"""Validate embedding timeouts without real HTTP requests."""

from __future__ import annotations

import httpx
import pytest
from pydantic import ValidationError

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.embeddings.factory import (
    create_embedding_provider,
)
from philosophy_influence_explorer.embeddings.gemini import (
    GeminiEmbeddingProvider,
)
from philosophy_influence_explorer.embeddings.ollama import (
    OllamaEmbeddingProvider,
)


@pytest.fixture(autouse=True)
def isolate_embedding_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EMBEDDING_TIMEOUT_SECONDS", raising=False)


def test_embedding_timeout_default() -> None:
    settings = Settings(_env_file=None, neo4j_enabled=False)

    assert settings.embedding_timeout_seconds == 60.0


@pytest.mark.parametrize(
    "value",
    [0, -1, float("inf"), float("-inf"), float("nan")],
)
def test_settings_reject_invalid_embedding_timeout(value: float) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            neo4j_enabled=False,
            embedding_timeout_seconds=value,
        )


def test_embedding_timeout_loads_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_TIMEOUT_SECONDS", "8.5")

    settings = Settings(_env_file=None, neo4j_enabled=False)

    assert settings.embedding_timeout_seconds == 8.5


@pytest.mark.parametrize("provider_name", ["gemini", "ollama"])
@pytest.mark.parametrize(
    "value",
    [0, -1, float("inf"), float("-inf"), float("nan")],
)
def test_provider_rejects_invalid_timeout_before_http(
    monkeypatch: pytest.MonkeyPatch,
    provider_name: str,
    value: float,
) -> None:
    def deny_http(*args, **kwargs):
        raise AssertionError("Unexpected HTTP request.")

    monkeypatch.setattr(httpx, "post", deny_http)

    with pytest.raises(
        ValueError,
        match="timeout_seconds must be positive and finite",
    ):
        if provider_name == "gemini":
            GeminiEmbeddingProvider(
                api_key="test-key",
                model="gemini-embedding-001",
                dimensions=768,
                timeout_seconds=value,
            )
        else:
            OllamaEmbeddingProvider(
                base_url="http://ollama.test",
                model="test-model",
                dimensions=768,
                timeout_seconds=value,
            )


@pytest.mark.parametrize("provider_name", ["gemini", "ollama"])
def test_factory_passes_configured_timeout_to_http(
    monkeypatch: pytest.MonkeyPatch,
    provider_name: str,
) -> None:
    captured_timeouts: list[float] = []

    def fake_post(url, *, json, timeout, headers=None):
        captured_timeouts.append(timeout)

        if provider_name == "gemini":
            payload = {
                "embedding": {
                    "values": [1.0] + [0.0] * 767,
                }
            }
        else:
            payload = {
                "embeddings": [
                    [1.0] + [0.0] * 767,
                ]
            }

        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    settings = Settings(
        _env_file=None,
        neo4j_enabled=False,
        embedding_provider=provider_name,
        embedding_model=(
            "gemini-embedding-001"
            if provider_name == "gemini"
            else "test-model"
        ),
        embedding_dimensions=768,
        embedding_timeout_seconds=8.5,
        google_api_key="test-key",
        ollama_base_url="http://ollama.test",
    )

    provider = create_embedding_provider(settings)
    vector = provider.embed_query("test")

    assert len(vector) == 768
    assert captured_timeouts == [8.5]
