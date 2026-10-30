"""Unit tests for bounded shared-concept graph context retrieval."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from neo4j import Query
from neo4j.exceptions import Neo4jError

from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextRetriever,
)
from philosophy_influence_explorer.retrieval.passage_indexer import DATASET_ID
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageSearchFilters,
)

_SEED_ID = "passage:hegel:wl:being:de"


class FakeSession:
    """Capture queries without pretending to execute Cypher."""

    def __init__(
        self,
        records: list[dict[str, object]],
        error: Exception | None = None,
    ) -> None:
        self.records = records
        self.error = error
        self.calls: list[tuple[str, dict[str, object]]] = []

    def run(
        self,
        query: Query,
        **parameters: object,
    ) -> list[dict[str, object]]:
        assert isinstance(query, Query)
        assert query.timeout == 7.0
        self.calls.append((query.text, parameters))
        if self.error is not None:
            raise self.error
        return self.records


class FakeClient:
    """Expose the client interface used by the retriever."""

    def __init__(
        self,
        records: list[dict[str, object]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.fake_session = FakeSession(
            records if records is not None else [],
            error,
        )

    def retrieval_query(self, text: str) -> Query:
        """Build a timed query for the fake session."""
        return Query(text, timeout=7.0)

    @contextmanager
    def session(self) -> Iterator[FakeSession]:
        yield self.fake_session


def _record(language: str = "en") -> dict[str, object]:
    related_id = f"passage:hegel:wl:being:{language}"
    concept_id = "concept:becoming"
    return {
        "seed_id": _SEED_ID,
        "concept": {
            "id": concept_id,
            "canonical_label": "becoming",
            "concept_family": "dialectic",
            "label_en": "becoming",
            "label_ru": "становление",
            "label_de": "Werden",
        },
        "seed_edge": {
            "id": "relation:passage:hegel:being:discusses:becoming",
            "from_id": _SEED_ID,
            "to_id": concept_id,
            "review_status": "reviewed",
            "extraction_method": "curated",
            "confidence": 1.0,
        },
        "related_edge": {
            "id": (
                f"relation:passage:hegel:being-{language}:"
                "discusses:becoming"
            ),
            "from_id": related_id,
            "to_id": concept_id,
            "review_status": "curated",
            "extraction_method": "editorial",
            "confidence": 1.0,
        },
        "passage": {
            "id": related_id,
            "text": "Editorial summary used as a unit-test fixture.",
            "source_id": "source:project-editorial",
            "work_id": "work:hegel:wissenschaft-der-logik",
            "citation_label": "Editorial summary of Being/Becoming",
            "language": language,
            "text_kind": "editorial_summary",
            "review_status": "curated",
            "is_verbatim": False,
            "is_editorial": True,
            "is_machine_generated": False,
        },
    }


def test_expand_maps_paths_and_preserves_edge_direction() -> None:
    client = FakeClient([_record("en"), _record("ru")])
    retriever = GraphContextRetriever(client=client)

    paths = retriever.expand([_SEED_ID])

    assert len(paths) == 2
    assert [path.passage.language for path in paths] == ["en", "ru"]
    assert paths[0].seed_id == _SEED_ID
    assert paths[0].concept.id == "concept:becoming"
    assert paths[0].seed_edge.from_id == _SEED_ID
    assert paths[0].seed_edge.to_id == paths[0].concept.id
    assert paths[0].related_edge.from_id == paths[0].passage.id
    assert paths[0].related_edge.to_id == paths[0].concept.id
    assert paths[0].seed_edge.review_status == "reviewed"
    assert paths[0].related_edge.review_status == "curated"
    assert paths[0].related_edge.relation_type == "DISCUSSES"
    assert paths[0].passage.text_kind == "editorial_summary"
    assert paths[0].passage.is_editorial is True
    assert paths[0].passage.is_verbatim is False
    assert not hasattr(paths[0].passage, "score")


def test_expand_binds_normalized_filters_and_seed_ids() -> None:
    client = FakeClient()
    retriever = GraphContextRetriever(client=client)

    retriever.expand(
        [f"  {_SEED_ID}  ", _SEED_ID],
        limit=3,
        filters=PassageSearchFilters(
            concept_family=" dialectic ",
            language=" ru ",
            is_verbatim=False,
            is_editorial=True,
        ),
    )

    assert len(client.fake_session.calls) == 1
    _, parameters = client.fake_session.calls[0]
    assert parameters == {
        "seed_ids": [_SEED_ID],
        "dataset_id": DATASET_ID,
        "allowed_edge_statuses": ["reviewed", "curated"],
        "language": "ru",
        "is_verbatim": False,
        "is_editorial": True,
        "concept_family": "dialectic",
        "limit": 3,
    }


def test_expand_query_scopes_nodes_edges_and_filters() -> None:
    client = FakeClient()
    GraphContextRetriever(client=client).expand([_SEED_ID])

    query, parameters = client.fake_session.calls[0]

    for entity in ("seed", "concept", "related", "seed_edge", "related_edge"):
        assert f"{entity}.dataset = $dataset_id" in query

    for edge in ("seed_edge", "related_edge"):
        assert f"{edge}.id IS NOT NULL" in query
        assert f"{edge}.review_status IN $allowed_edge_statuses" in query

    assert "related.id <> seed.id" in query
    assert "related.language = $language" in query
    assert "related.is_verbatim = $is_verbatim" in query
    assert "related.is_editorial = $is_editorial" in query
    assert "concept.concept_family = $concept_family" in query
    assert "WITH DISTINCT seed, concept, seed_edge, related_edge, related" in query
    assert query.index("ORDER BY") < query.index("LIMIT $limit")
    assert parameters["language"] is None
    assert parameters["concept_family"] is None
    assert parameters["is_verbatim"] is None
    assert parameters["is_editorial"] is None
    assert parameters["limit"] == 20


def test_expand_returns_empty_when_database_has_no_paths() -> None:
    client = FakeClient()

    assert GraphContextRetriever(client=client).expand([_SEED_ID]) == []
    assert len(client.fake_session.calls) == 1


def test_expand_empty_seeds_does_not_contact_database() -> None:
    client = FakeClient()

    assert GraphContextRetriever(client=client).expand([]) == []
    assert client.fake_session.calls == []


@pytest.mark.parametrize(
    ("seed_ids", "limit", "message"),
    [
        ([_SEED_ID], 0, "limit must be at least 1"),
        (["   "], 3, "seed_ids must not contain blank IDs"),
        ([_SEED_ID, ""], 3, "seed_ids must not contain blank IDs"),
    ],
)
def test_expand_rejects_invalid_input_before_database_calls(
    seed_ids: list[str],
    limit: int,
    message: str,
) -> None:
    client = FakeClient()
    retriever = GraphContextRetriever(client=client)

    with pytest.raises(ValueError, match=message):
        retriever.expand(seed_ids, limit=limit)

    assert client.fake_session.calls == []


def test_expand_wraps_neo4j_errors() -> None:
    error = Neo4jError("Database unavailable")
    client = FakeClient(error=error)

    with pytest.raises(
        RuntimeError,
        match="Unable to retrieve graph context from Neo4j",
    ) as captured:
        GraphContextRetriever(client=client).expand([_SEED_ID])

    assert captured.value.__cause__ is error
