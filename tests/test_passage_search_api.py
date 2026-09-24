"""API tests for concept-aware semantic Passage retrieval."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from philosophy_influence_explorer.api.dependencies import (
    get_passage_retriever,
)
from philosophy_influence_explorer.main import create_app
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageSearchFilters,
)


@dataclass(frozen=True)
class FakePassageConcept:
    """Minimal Concept data matching the API route's read contract."""

    id: str
    canonical_label: str
    concept_family: str
    label_en: str
    label_ru: str
    label_de: str


@dataclass(frozen=True)
class FakeRetrievedPassage:
    """Minimal Passage data matching the API route's read contract."""

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
    concepts: tuple[FakePassageConcept, ...]


class FakePassageRetriever:
    """Controlled semantic retriever substitute for route tests."""

    def __init__(
        self,
        passages: list[FakeRetrievedPassage] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.passages = passages or []
        self.error = error
        self.calls: list[tuple[str, int, PassageSearchFilters]] = []

    def search(
        self,
        query_text: str,
        *,
        limit: int = 5,
        filters: PassageSearchFilters | None = None,
    ) -> list[FakeRetrievedPassage]:
        """Capture request parameters and return configured results or error."""
        self.calls.append(
            (
                query_text,
                limit,
                filters or PassageSearchFilters(),
            )
        )

        if self.error is not None:
            raise self.error

        return self.passages


def make_client(retriever: FakePassageRetriever) -> TestClient:
    """Create an app client with its retriever dependency overridden."""
    app = create_app()
    app.dependency_overrides[get_passage_retriever] = lambda: retriever
    return TestClient(app)


def _passage() -> FakeRetrievedPassage:
    """Build one complete fake API result."""
    return FakeRetrievedPassage(
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
        concepts=(
            FakePassageConcept(
                id="concept:becoming",
                canonical_label="becoming",
                concept_family="dialectic",
                label_en="becoming",
                label_ru="становление",
                label_de="Werden",
            ),
        ),
    )


def test_search_returns_results_concepts_and_filters() -> None:
    """Endpoint should serialize concepts and bind all optional filters."""
    retriever = FakePassageRetriever(passages=[_passage()])

    with make_client(retriever) as client:
        response = client.get(
            "/api/v1/passages/search",
            params={
                "q": "  being, nothing, and becoming  ",
                "limit": 3,
                "concept_family": " dialectic ",
                "language": " en ",
                "is_verbatim": "false",
                "is_editorial": "true",
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
                "concepts": [
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
        ],
    }
    assert retriever.calls == [
        (
            "being, nothing, and becoming",
            3,
            PassageSearchFilters(
                concept_family=" dialectic ",
                language=" en ",
                is_verbatim=False,
                is_editorial=True,
            ),
        )
    ]


def test_search_allows_unfiltered_requests() -> None:
    """Existing unfiltered calls should remain backwards compatible."""
    retriever = FakePassageRetriever(passages=[])

    with make_client(retriever) as client:
        response = client.get(
            "/api/v1/passages/search",
            params={"q": "being"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "query": "being",
        "count": 0,
        "results": [],
    }
    assert retriever.calls == [
        ("being", 5, PassageSearchFilters())
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
    """FastAPI validation should reject out-of-range limits."""
    retriever = FakePassageRetriever()

    with make_client(retriever) as client:
        response = client.get(
            "/api/v1/passages/search",
            params={"q": "being", "limit": 21},
        )

    assert response.status_code == 422
    assert retriever.calls == []


def test_search_maps_provider_or_database_failures_to_503() -> None:
    """Infrastructure failures should not expose internal details."""
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
    assert retriever.calls == [
        ("being", 5, PassageSearchFilters())
    ]
