"""Tests for semantic retrieval of curated Passage nodes."""

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
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageRetriever,
)


class FakeProvider(EmbeddingProvider):
    """Deterministic query embedding provider for retriever tests."""

    @property
    def model_info(self) -> EmbeddingModelInfo:
        """Describe the fake query-vector contract."""
        return EmbeddingModelInfo(
            provider="fake",
            model="fake-model",
            dimensions=3,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Unused by retrieval tests."""
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        """Return a predictable embedding for a normalized query."""
        assert text == "freedom and morality"
        return [0.1, 0.2, 0.3]


class FakeResult:
    """Minimal iterable result returned by FakeSession."""

    def __init__(self, records: list[dict[str, object]]) -> None:
        self._records = records

    def __iter__(self) -> Iterator[dict[str, object]]:
        return iter(self._records)


class FakeSession:
    """Record Cypher calls and return prepared vector-search rows."""

    def __init__(self, records: list[dict[str, object]]) -> None:
        self._records = records
        self.calls: list[tuple[str, dict[str, object]]] = []

    def run(
        self,
        query: str,
        **parameters: object,
    ) -> FakeResult:
        """Capture the retrieval query and its bound parameters."""
        self.calls.append((query, parameters))
        return FakeResult(self._records)


class FakeClient:
    """Expose the context-managed session surface used by PassageRetriever."""

    def __init__(self, records: list[dict[str, object]]) -> None:
        self.fake_session = FakeSession(records)

    @contextmanager
    def session(self) -> Iterator[FakeSession]:
        """Yield the fake session."""
        yield self.fake_session


def test_search_embeds_query_and_returns_ranked_passages() -> None:
    """Search should bind vector-index parameters and map Neo4j rows."""
    client = FakeClient(
        [
            {
                "id": "passage:kants-autonomy",
                "text": "Autonomy is the ground of moral obligation.",
                "score": 0.92134,
                "source_id": "source:kant:groundwork",
                "work_id": "work:kants-groundwork",
                "citation_label": "Groundwork, 4:440",
                "language": "en",
                "text_kind": "editorial_summary",
                "is_verbatim": False,
                "is_editorial": True,
                "is_machine_generated": False,
            },
            {
                "id": "passage:mill-liberty",
                "text": "Individual liberty has broad social value.",
                "score": 0.81234,
                "source_id": "source:mill:on-liberty",
                "work_id": "work:mills-on-liberty",
                "citation_label": "On Liberty, chapter 1",
                "language": "en",
                "text_kind": "editorial_summary",
                "is_verbatim": False,
                "is_editorial": True,
                "is_machine_generated": False,
            },
        ]
    )
    retriever = PassageRetriever(
        client=client,
        provider=FakeProvider(),
    )

    passages = retriever.search(
        "  freedom and morality  ",
        limit=2,
    )

    assert [(passage.id, passage.score) for passage in passages] == [
        ("passage:kants-autonomy", 0.92134),
        ("passage:mill-liberty", 0.81234),
    ]
    assert passages[0].work_id == "work:kants-groundwork"
    assert passages[0].citation_label == "Groundwork, 4:440"
    assert passages[1].source_id == "source:mill:on-liberty"
    assert passages[1].is_editorial is True

    assert len(client.fake_session.calls) == 1
    query, parameters = client.fake_session.calls[0]

    assert "db.index.vector.queryNodes" in query
    assert "node.dataset = $dataset_id" in query
    assert "node.embedding_model = $model" in query
    assert "node.source_id AS source_id" in query
    assert "node.work_id AS work_id" in query
    assert "node.citation_label AS citation_label" in query
    assert "node.author AS author" not in query
    assert "node.source AS source" not in query
    assert "node.work AS work" not in query
    assert parameters == {
        "index_name": PASSAGE_EMBEDDING_INDEX,
        "candidate_limit": 8,
        "query_embedding": [0.1, 0.2, 0.3],
        "dataset_id": DATASET_ID,
        "provider": "fake",
        "model": "fake-model",
        "dimensions": 3,
        "limit": 2,
    }


@pytest.mark.parametrize(
    ("query_text", "limit", "message"),
    [
        ("   ", 5, "query_text must not be blank"),
        ("freedom", 0, "limit must be at least 1"),
    ],
)
def test_search_rejects_invalid_input_before_external_calls(
    query_text: str,
    limit: int,
    message: str,
) -> None:
    """Invalid input must fail before Ollama or Neo4j are contacted."""
    client = FakeClient([])
    retriever = PassageRetriever(
        client=client,
        provider=FakeProvider(),
    )

    with pytest.raises(ValueError, match=message):
        retriever.search(query_text, limit=limit)

    assert client.fake_session.calls == []


def test_search_rejects_query_vector_with_wrong_dimension() -> None:
    """A provider contract breach must stop before running Cypher."""

    class InvalidDimensionProvider(FakeProvider):
        def embed_query(self, text: str) -> list[float]:
            return [0.1, 0.2]

    client = FakeClient([])
    retriever = PassageRetriever(
        client=client,
        provider=InvalidDimensionProvider(),
    )

    with pytest.raises(RuntimeError, match="unexpected dimension"):
        retriever.search("freedom and morality")

    assert client.fake_session.calls == []
