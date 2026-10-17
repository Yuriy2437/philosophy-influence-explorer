"""Isolated tests for Gemini embeddings; no real API calls."""

from __future__ import annotations

import httpx
import pytest

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.embeddings.factory import (
    create_embedding_provider,
)
from philosophy_influence_explorer.embeddings.gemini import (
    GeminiEmbeddingProvider,
    GeminiEmbeddingProviderError,
)


def make_provider() -> GeminiEmbeddingProvider:
    return GeminiEmbeddingProvider(
        api_key="test-key",
        model="gemini-embedding-001",
        dimensions=768,
        timeout_seconds=5.0,
    )


def make_response(payload: object, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("POST", "https://example.test/embed")
    return httpx.Response(
        status_code=status_code,
        json=payload,
        request=request,
    )


def test_factory_creates_gemini_provider() -> None:
    settings = Settings(
        _env_file=None,
        neo4j_enabled=False,
        embedding_provider="gemini",
        embedding_model="gemini-embedding-001",
        embedding_dimensions=768,
        google_api_key="test-key",
    )

    provider = create_embedding_provider(settings)

    assert isinstance(provider, GeminiEmbeddingProvider)
    assert provider.model_info.provider == "gemini"
    assert provider.model_info.dimensions == 768


def test_factory_rejects_missing_key() -> None:
    settings = Settings(
        _env_file=None,
        neo4j_enabled=False,
        embedding_provider="gemini",
        google_api_key=None,
    )

    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        create_embedding_provider(settings)


@pytest.mark.parametrize(
    ("method", "task_type"),
    [
        ("embed_query", "RETRIEVAL_QUERY"),
        ("embed_documents", "RETRIEVAL_DOCUMENT"),
    ],
)
def test_request_and_normalization(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    task_type: str,
) -> None:
    captured: dict[str, object] = {}

    def fake_post(url, *, headers, json, timeout):
        captured.update(
            url=url,
            headers=headers,
            body=json,
            timeout=timeout,
        )
        return make_response(
            {"embedding": {"values": [3.0, 4.0] + [0.0] * 766}}
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = make_provider()
    if method == "embed_query":
        vector = provider.embed_query("test")
    else:
        vector = provider.embed_documents(["test"])[0]

    assert len(vector) == 768
    assert vector[:2] == pytest.approx([0.6, 0.8])
    assert captured == {
        "url": (
            "https://generativelanguage.googleapis.com/v1beta/"
            "models/gemini-embedding-001:embedContent"
        ),
        "headers": {"x-goog-api-key": "test-key"},
        "body": {
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": "test"}]},
            "taskType": task_type,
            "outputDimensionality": 768,
        },
        "timeout": 5.0,
    }


def test_empty_documents_do_not_call_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Unexpected HTTP call.")

    monkeypatch.setattr(httpx, "post", fail_if_called)

    assert make_provider().embed_documents([]) == []


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"embedding": {"values": [1.0]}},
        {"embedding": {"values": [True] * 768}},
        {"embedding": {"values": ["invalid"] * 768}},
        {"embedding": {"values": [0.0] * 768}},
    ],
)
def test_rejects_invalid_vectors(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: make_response(payload),
    )

    with pytest.raises(GeminiEmbeddingProviderError):
        make_provider().embed_query("test")


def test_http_error_does_not_expose_response_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: make_response(
            {"error": {"message": "sensitive-response-marker"}},
            status_code=429,
        ),
    )

    with pytest.raises(GeminiEmbeddingProviderError) as caught:
        make_provider().embed_query("test")

    assert "HTTP 429" in str(caught.value)
    assert "sensitive-response-marker" not in str(caught.value)


def test_transport_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args, **kwargs):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(httpx, "post", fail)

    with pytest.raises(
        GeminiEmbeddingProviderError,
        match="Could not reach",
    ):
        make_provider().embed_query("test")
