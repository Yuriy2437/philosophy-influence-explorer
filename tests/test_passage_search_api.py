"""API tests for semantic Passage retrieval."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from philosophy_influence_explorer.api.dependencies import (
    get_passage_retriever,
)
from philosophy_influence_explorer.main import create_app


@dataclass(frozen=True)
class FakeRetrievedPassage:
    """A minimal passage object matching the route's read contract."""

    id: str
    text: str
    score: float
    source_id: str
    work_id: str
    citation_label: str
    language: str
    text_kind: str
    is_verbatim: bool
    is_editorial: bool
    is_machine_generated: bool


class FakePassageRetriever:
    """Controlled semantic retriever substitute for route tests."""

    def __init__(
        self,
        passages: list[FakeRetrievedPassage] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.passages = passages or []
        self.error = error
        self.calls: list[tuple[str, int]] = []

    def search(
        self,
        query_text: str,
        *,
        limit: int = 5,
    ) -> list[FakeRetrievedPassage]:
        """Capture the request and return configured results or an error."""
        self.calls.append((query_text, limit))

        if self.error is not None:
            raise self.error

        return self.passages


def make_client(retriever: FakePassageRetriever) -> TestClient:
    """Create an app client whose semantic-retrieval dependency is overridden."""
    app = create_app()
    app.dependency_overrides[get_passage_retriever] = lambda: retriever
    return TestClient(app)


def test_search_returns_schema_aligned_semantic_results() -> None:
    """The endpoint should serialize the retriever's provenanced results."""
    retriever = FakePassageRetriever(
        passages=[
            FakeRetrievedPassage(
                id="passage:hegel:wl:being:en",
                text="Becoming unites being and nothing.",
                score=0.8767,
                source_id="source:project-editorial",
                work_id="work:hegel:wissenschaft-der-logik",
                citation_label="Editorial summary of Wissenschaft der Logik",
                language="en",
                text_kind="editorial_summary",
                is_verbatim=False,
                is_editorial=True,
                is_machine_generated=False,
            )
        ]
    )

    with make_client(retriever) as client:
        response = client.get(
            "/api/v1/passages/search",
            params={
                "q": "  being, nothing, and becoming  ",
                "limit": 3,
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json; charset=utf-8"
    assert response.json() == {
        "query": "being, nothing, and becoming",
        "count": 1,
        "results": [
            {
                "id": "passage:hegel:wl:being:en",
                "text": "Becoming unites being and nothing.",
                "score": 0.8767,
                "source_id": "source:project-editorial",
                "work_id": "work:hegel:wissenschaft-der-logik",
                "citation_label": "Editorial summary of Wissenschaft der Logik",
                "language": "en",
                "text_kind": "editorial_summary",
                "is_verbatim": False,
                "is_editorial": True,
                "is_machine_generated": False,
            }
        ],
    }
    assert retriever.calls == [
        ("being, nothing, and becoming", 3)
    ]


def test_search_rejects_a_whitespace_only_query() -> None:
    """Whitespace-only input should not reach the retriever."""
    retriever = FakePassageRetriever()

    with make_client(retriever) as client:
        response = client.get(
            "/api/v1/passages/search",
            params={"q": "   "},
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Query parameter 'q' must not be blank."
    }
    assert retriever.calls == []


def test_search_rejects_an_invalid_limit_before_retrieval() -> None:
    """FastAPI validation should reject limits outside the endpoint contract."""
    retriever = FakePassageRetriever()

    with make_client(retriever) as client:
        response = client.get(
            "/api/v1/passages/search",
            params={"q": "being", "limit": 21},
        )

    assert response.status_code == 422
    assert retriever.calls == []


def test_search_maps_provider_or_database_failures_to_503() -> None:
    """Infrastructure retrieval failures should not expose internals."""
    retriever = FakePassageRetriever(
        error=RuntimeError("Ollama timed out while embedding query."),
    )

    with make_client(retriever) as client:
        response = client.get(
            "/api/v1/passages/search",
            params={"q": "being"},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Semantic search service is temporarily unavailable."
    }
    assert retriever.calls == [("being", 5)]
