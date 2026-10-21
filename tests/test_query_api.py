"""API tests for retrieval-only semantic and graph queries."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from philosophy_influence_explorer.api.dependencies import (
    get_semantic_graph_retriever,
)
from philosophy_influence_explorer.main import create_app
from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextEdge,
    GraphContextPassage,
    GraphContextPath,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageConcept,
    PassageSearchFilters,
    RetrievedPassage,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphResult,
)


class FakeQueryRetriever:
    """Capture the API contract without calling embeddings or Neo4j."""

    def __init__(
        self,
        result: SemanticGraphResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = (
            result
            if result is not None
            else SemanticGraphResult(semantic_passages=(), graph_context=())
        )
        self.error = error
        self.calls: list[
            tuple[str, int, int, PassageSearchFilters | None]
        ] = []

    def retrieve(
        self,
        query_text: str,
        *,
        limit: int = 5,
        graph_limit: int = 20,
        filters: PassageSearchFilters | None = None,
    ) -> SemanticGraphResult:
        self.calls.append((query_text, limit, graph_limit, filters))
        if self.error is not None:
            raise self.error
        return self.result


def make_client(retriever: FakeQueryRetriever) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_semantic_graph_retriever] = lambda: retriever
    return TestClient(app)


def _result() -> SemanticGraphResult:
    """Build a complete result with explicitly synthetic fixture text."""
    concept = PassageConcept(
        id="concept:becoming",
        canonical_label="becoming",
        concept_family="dialectic",
        label_en="becoming",
        label_ru="становление",
        label_de="Werden",
    )
    seed_id = "passage:hegel:wl:being:de"
    related_id = "passage:hegel:wl:being:en"

    seed = RetrievedPassage(
        id=seed_id,
        text="Synthetic primary-text fixture.",
        score=0.854,
        source_id="source:test-primary",
        work_id="work:hegel:wissenschaft-der-logik",
        citation_label="Test primary citation",
        language="de",
        text_kind="primary_quote",
        review_status="reviewed",
        is_verbatim=True,
        is_editorial=False,
        is_machine_generated=False,
        concepts=(concept,),
    )

    related = GraphContextPassage(
        id=related_id,
        text="Synthetic editorial fixture.",
        source_id="source:test-editorial",
        work_id="work:hegel:wissenschaft-der-logik",
        citation_label="Test editorial citation",
        language="en",
        text_kind="editorial_summary",
        review_status="curated",
        is_verbatim=False,
        is_editorial=True,
        is_machine_generated=False,
    )

    path = GraphContextPath(
        seed_id=seed_id,
        concept=concept,
        seed_edge=GraphContextEdge(
            id="relation:test:seed",
            from_id=seed_id,
            to_id=concept.id,
            review_status="reviewed",
            extraction_method="curated",
            confidence=1.0,
        ),
        related_edge=GraphContextEdge(
            id="relation:test:related",
            from_id=related_id,
            to_id=concept.id,
            review_status="curated",
            extraction_method="editorial",
            confidence=1.0,
        ),
        passage=related,
    )

    return SemanticGraphResult(
        semantic_passages=(seed,),
        graph_context=(path,),
    )


def test_query_serializes_semantic_results_and_graph_paths() -> None:
    retriever = FakeQueryRetriever(result=_result())

    with make_client(retriever) as client:
        response = client.post(
            "/api/v1/query",
            json={
                "q": "  becoming  ",
                "limit": 3,
                "graph_limit": 7,
                "language": " de ",
                "concept_family": " dialectic ",
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json; charset=utf-8"

    payload = response.json()
    assert payload["query"] == "becoming"
    assert payload["mode"] == "retrieval_only"
    assert payload["semantic_count"] == 1
    assert payload["graph_path_count"] == 1
    assert "answer" not in payload

    seed = payload["semantic_passages"][0]
    path = payload["graph_context"][0]

    assert seed["score"] == 0.854
    assert seed["concepts"][0]["id"] == "concept:becoming"
    assert path["seed_id"] == seed["id"]
    assert path["seed_edge"]["from_id"] == seed["id"]
    assert path["related_edge"]["from_id"] == path["passage"]["id"]
    assert path["related_edge"]["to_id"] == path["concept"]["id"]
    assert path["related_edge"]["relation_type"] == "DISCUSSES"
    assert path["passage"]["text_kind"] == "editorial_summary"
    assert "score" not in path["passage"]

    assert retriever.calls == [
        (
            "becoming",
            3,
            7,
            PassageSearchFilters(
                language=" de ",
                concept_family=" dialectic ",
            ),
        )
    ]


def test_query_empty_result_and_default_parameters() -> None:
    retriever = FakeQueryRetriever()

    with make_client(retriever) as client:
        response = client.post("/api/v1/query", json={"q": "becoming"})

    assert response.status_code == 200
    assert response.json() == {
        "query": "becoming",
        "mode": "retrieval_only",
        "semantic_count": 0,
        "graph_path_count": 0,
        "semantic_passages": [],
        "graph_context": [],
    }
    assert retriever.calls == [
        ("becoming", 5, 20, PassageSearchFilters())
    ]


def test_query_binds_primary_only_filters() -> None:
    retriever = FakeQueryRetriever()

    with make_client(retriever) as client:
        response = client.post(
            "/api/v1/query",
            json={
                "q": "becoming",
                "is_verbatim": True,
                "is_editorial": False,
            },
        )

    assert response.status_code == 200
    assert retriever.calls[0][3] == PassageSearchFilters(
        is_verbatim=True,
        is_editorial=False,
    )


def test_query_rejects_blank_before_retrieval() -> None:
    retriever = FakeQueryRetriever()

    with make_client(retriever) as client:
        response = client.post("/api/v1/query", json={"q": "   "})

    assert response.status_code == 400
    assert retriever.calls == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"q": ""},
        {"q": "x" * 501},
        {"q": "becoming", "limit": 0},
        {"q": "becoming", "limit": 21},
        {"q": "becoming", "graph_limit": 0},
        {"q": "becoming", "graph_limit": 21},
    ],
)
def test_query_rejects_invalid_request_before_retrieval(
    body: dict[str, object],
) -> None:
    retriever = FakeQueryRetriever()

    with make_client(retriever) as client:
        response = client.post("/api/v1/query", json=body)

    assert response.status_code == 422
    assert retriever.calls == []


def test_query_hides_infrastructure_error_details() -> None:
    retriever = FakeQueryRetriever(
        error=RuntimeError("Private infrastructure error detail")
    )

    with make_client(retriever) as client:
        response = client.post("/api/v1/query", json={"q": "becoming"})

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Query retrieval service is temporarily unavailable."
    }
    assert "Private infrastructure" not in response.text


def test_query_maps_retriever_value_error_to_400() -> None:
    retriever = FakeQueryRetriever(error=ValueError("Invalid retrieval input"))

    with make_client(retriever) as client:
        response = client.post("/api/v1/query", json={"q": "becoming"})

    assert response.status_code == 400


def test_query_get_is_not_supported() -> None:
    retriever = FakeQueryRetriever()

    with make_client(retriever) as client:
        response = client.get("/api/v1/query")

    assert response.status_code == 405
    assert retriever.calls == []


def test_query_openapi_describes_retrieval_only_contract() -> None:
    retriever = FakeQueryRetriever()

    with make_client(retriever) as client:
        response = client.get("/openapi.json")

    document = response.json()
    operation = document["paths"]["/api/v1/query"]["post"]
    properties = document["components"]["schemas"]["QueryResponse"]["properties"]

    assert "requestBody" in operation
    assert "503" in operation["responses"]
    assert "semantic_passages" in properties
    assert "graph_context" in properties
    assert "answer" not in properties
