"""Tests for controlled Passage embedding indexing."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from philosophy_influence_explorer.embeddings.base import (
    EmbeddingModelInfo,
    EmbeddingProvider,
)
from philosophy_influence_explorer.retrieval.passage_indexer import (
    DATASET_ID,
    PASSAGE_EMBEDDING_INDEX,
    PassageForEmbedding,
    batched,
    index_curated_passage_embeddings,
)


class FakeProvider(EmbeddingProvider):
    """Deterministic embedding provider for indexer unit tests."""

    @property
    def model_info(self) -> EmbeddingModelInfo:
        """Describe the fake vectors used by tests."""
        return EmbeddingModelInfo(
            provider="fake",
            model="fake-model",
            dimensions=3,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one predictable vector per text."""
        return [
            [float(index), 0.0, 1.0]
            for index, _ in enumerate(texts, start=1)
        ]

    def embed_query(self, text: str) -> list[float]:
        """Return a predictable query vector."""
        return [1.0, 0.0, 1.0]


class FakeResult:
    """Minimal iterable result used by the fake Neo4j session."""

    def __init__(self, records: list[dict[str, str]]) -> None:
        self._records = records

    def __iter__(self) -> Iterator[dict[str, str]]:
        return iter(self._records)

    def consume(self) -> None:
        """Match the Neo4j result interface used by the indexer."""


class FakeSession:
    """Record queries and return configured Passage rows."""

    def __init__(self, records: list[dict[str, str]]) -> None:
        self.records = records
        self.calls: list[tuple[str, dict[str, object]]] = []

    def run(self, query: str, **parameters: object) -> FakeResult:
        """Store every query and return rows only for Passage loading."""
        self.calls.append((query, parameters))

        if "RETURN passage.id AS id" in query:
            return FakeResult(self.records)

        return FakeResult([])


class FakeClient:
    """Expose the same session context manager surface as Neo4jClient."""

    def __init__(self, records: list[dict[str, str]]) -> None:
        self.fake_session = FakeSession(records)

    @contextmanager
    def session(self) -> Iterator[FakeSession]:
        """Yield the fake session used for all indexer operations."""
        yield self.fake_session


def test_batched_splits_values_without_changing_order() -> None:
    """Batching should preserve a deterministic Passage ordering."""
    passages = [
        PassageForEmbedding(id=f"passage:{index}", text=f"text {index}")
        for index in range(1, 6)
    ]

    result = list(batched(passages, batch_size=2))

    assert [[passage.id for passage in batch] for batch in result] == [
        ["passage:1", "passage:2"],
        ["passage:3", "passage:4"],
        ["passage:5"],
    ]


def test_indexer_creates_index_loads_and_persists_embeddings() -> None:
    """Eligible passages are indexed with provider/model metadata."""
    client = FakeClient(
        [
            {"id": "passage:alpha", "text": "Alpha text"},
            {"id": "passage:beta", "text": "Beta text"},
            {"id": "passage:gamma", "text": "Gamma text"},
        ]
    )

    summary = index_curated_passage_embeddings(
        client=client,
        provider=FakeProvider(),
        batch_size=2,
    )

    assert summary.eligible == 3
    assert summary.indexed == 3
    assert summary.skipped == 0

    queries = [query for query, _ in client.fake_session.calls]
    parameters = [parameters for _, parameters in client.fake_session.calls]

    assert any(
        f"CREATE VECTOR INDEX {PASSAGE_EMBEDDING_INDEX} IF NOT EXISTS" in query
        for query in queries
    )
    assert any(
        "MATCH (passage:Passage {dataset: $dataset_id})" in query
        for query in queries
    )

    update_calls = [
        parameters
        for query, parameters in client.fake_session.calls
        if "SET passage.embedding = row.embedding" in query
    ]

    assert len(update_calls) == 2
    assert update_calls[0]["dataset_id"] == DATASET_ID
    assert update_calls[0]["provider"] == "fake"
    assert update_calls[0]["model"] == "fake-model"
    assert update_calls[0]["dimensions"] == 3

    assert update_calls[0]["rows"] == [
        {"id": "passage:alpha", "embedding": [1.0, 0.0, 1.0]},
        {"id": "passage:beta", "embedding": [2.0, 0.0, 1.0]},
    ]
    assert update_calls[1]["rows"] == [
        {"id": "passage:gamma", "embedding": [1.0, 0.0, 1.0]},
    ]


def test_indexer_rejects_invalid_batch_size() -> None:
    """Batch size must be positive before any database work begins."""
    with pytest.raises(ValueError, match="batch_size must be at least 1"):
        index_curated_passage_embeddings(
            client=FakeClient([]),
            provider=FakeProvider(),
            batch_size=0,
        )
