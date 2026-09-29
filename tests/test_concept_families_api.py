"""Tests for the curated concept families endpoint."""

from contextlib import contextmanager
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neo4j.exceptions import Neo4jError

from philosophy_influence_explorer.api.routes import concepts
from philosophy_influence_explorer.main import create_app


class FakeSession:
    def __init__(
        self,
        families: list[str],
        error: Neo4jError | None = None,
    ) -> None:
        self.families = families
        self.error = error
        self.query: str | None = None
        self.parameters: dict[str, Any] | None = None

    def run(self, query: str, **parameters: Any) -> list[dict[str, str]]:
        self.query = query
        self.parameters = parameters

        if self.error is not None:
            raise self.error

        return [{"family": family} for family in self.families]


class FakeNeo4jClient:
    def __init__(self, session: FakeSession) -> None:
        self.fake_session = session

    @contextmanager
    def session(self):
        yield self.fake_session


@pytest.mark.parametrize(
    ("families", "expected"),
    [
        (
            ["dialectic", "epistemology", "ethics"],
            {"families": ["dialectic", "epistemology", "ethics"]},
        ),
        ([], {"families": []}),
    ],
)
def test_list_concept_families(
    monkeypatch: pytest.MonkeyPatch,
    families: list[str],
    expected: dict[str, list[str]],
) -> None:
    """Return graph-provided families without a hardcoded fallback."""
    fake_session = FakeSession(families)
    fake_client = FakeNeo4jClient(fake_session)

    monkeypatch.setattr(
        concepts,
        "get_neo4j_client",
        lambda request: fake_client,
    )

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/concepts/families")

    assert response.status_code == 200
    assert response.json() == expected
    assert fake_session.parameters == {"dataset": "curated_corpus_v1"}
    assert fake_session.query is not None
    assert "MATCH (concept:Concept {dataset: $dataset})" in fake_session.query
    assert "RETURN DISTINCT concept.concept_family AS family" in fake_session.query
    assert "ORDER BY family" in fake_session.query


def test_list_concept_families_handles_neo4j_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Neo4j query error should return 503 without exposing its details."""
    fake_session = FakeSession([], error=Neo4jError("Database unavailable"))
    fake_client = FakeNeo4jClient(fake_session)

    monkeypatch.setattr(
        concepts,
        "get_neo4j_client",
        lambda request: fake_client,
    )

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/concepts/families")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Concept families are temporarily unavailable."
    }
