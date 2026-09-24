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
    PassageSearchFilters,
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


def _record(
    *,
    id: str = "passage:hegel:wl:being:en",
    concepts: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    """Build one schema-aligned fake Neo4j row."""
    return {
        "id": id,
        "text": "Becoming unites being and nothing.",
        "score": 0.92134,
        "source_id": "source:project-editorial",
        "work_id": "work:hegel:wissenschaft-der-logik",
        "citation_label": "Editorial summary of Wissenschaft der Logik",
        "language": "en",
        "text_kind": "editorial_summary",
        "is_verbatim": False,
        "is_editorial": True,
        "is_machine_generated": False,
        "concepts": concepts
        or [
            {
                "id": "concept:becoming",
                "canonical_label": "becoming",
                "concept_family": "dialectic",
                "label_en": "becoming",
                "label_ru": "становление",
                "label_de": "Werden",
            }
        ],
    }


def test_search_returns_passages_with_graph_concepts_and_filters() -> None:
    """Search should map concept provenance and bind every optional filter."""
    client = FakeClient([_record()])
    retriever = PassageRetriever(
        client=client,
        provider=FakeProvider(),
    )

    passages = retriever.search(
        "  freedom and morality  ",
        limit=2,
        filters=PassageSearchFilters(
            concept_family="  dialectic  ",
            language=" en ",
            is_verbatim=False,
            is_editorial=True,
        ),
    )

    assert [(passage.id, passage.score) for passage in passages] == [
        ("passage:hegel:wl:being:en", 0.92134),
    ]
    assert passages[0].concepts[0].canonical_label == "becoming"
    assert passages[0].concepts[0].concept_family == "dialectic"
    assert passages[0].concepts[0].label_ru == "становление"

    assert len(client.fake_session.calls) == 1
    query, parameters = client.fake_session.calls[0]

    assert "db.index.vector.queryNodes" in query
    assert "(node)-[:DISCUSSES]->(concept:Concept" in query
    assert "$concept_family IS NULL" in query
    assert "node.language = $language" in query
    assert "node.is_verbatim = $is_verbatim" in query
    assert "node.is_editorial = $is_editorial" in query
    assert parameters == {
        "index_name": PASSAGE_EMBEDDING_INDEX,
        "candidate_limit": 8,
        "query_embedding": [0.1, 0.2, 0.3],
        "dataset_id": DATASET_ID,
        "provider": "fake",
        "model": "fake-model",
        "dimensions": 3,
        "language": "en",
        "is_verbatim": False,
        "is_editorial": True,
        "concept_family": "dialectic",
        "limit": 2,
    }


def test_search_uses_absent_filters_by_default() -> None:
    """Unfiltered search should bind None for every optional filter."""
    client = FakeClient([_record()])
    retriever = PassageRetriever(
        client=client,
        provider=FakeProvider(),
    )

    passages = retriever.search("freedom and morality")

    assert len(passages) == 1
    _, parameters = client.fake_session.calls[0]
    assert parameters["language"] is None
    assert parameters["is_verbatim"] is None
    assert parameters["is_editorial"] is None
    assert parameters["concept_family"] is None


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
