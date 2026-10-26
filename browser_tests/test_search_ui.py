"""Browser checks using real application assets and mocked API responses."""

import pytest
from playwright.sync_api import Page, expect


def test_search_page_loads_without_javascript_errors_or_retrieval(
    page: Page,
    search_ui,
) -> None:
    """Execute the UI script without contacting retrieval services."""
    response = page.goto("http://ui.test/search")
    assert response is not None
    assert response.status == 200

    expect(
        page.get_by_role("heading", name="Concept-aware semantic search", exact=True)
    ).to_be_visible()
    expect(page.locator("#search-form")).to_be_visible()
    expect(page.locator('#concept-family option[value="dialectic"]')).to_have_count(1)
    expect(page.locator('#limit option[value="1"]')).to_have_count(1)
    expect(page.locator("#limit")).to_have_value("5")
    expect(page.locator("#results")).to_be_empty()
    expect(page.locator("#status")).to_be_empty()

    assert search_ui.served_paths == {
        "/search",
        "/static/search.js",
        "/static/search.css",
        "/api/v1/concepts/families",
    }
    assert search_ui.query_requests == []
    assert search_ui.console_errors == []


@pytest.mark.parametrize(
    "graph_path_count",
    [2, 0],
    ids=["grouped-graph", "empty-graph"],
)
def test_search_renders_semantic_and_graph_results(
    page: Page,
    search_ui,
    graph_path_count: int,
) -> None:
    """Keep semantic results visible with populated or empty graph context."""

    seed_id = "passage:test:seed"
    related_id = "passage:test:related"

    seed = {
        "id": seed_id,
        "text": "Synthetic semantic fixture.",
        "score": 0.875,
        "source_id": "source:test:seed",
        "work_id": "work:test",
        "citation_label": "Synthetic semantic citation",
        "language": "en",
        "text_kind": "editorial_summary",
        "review_status": "candidate",
        "is_verbatim": False,
        "is_editorial": True,
        "is_machine_generated": False,
        "concepts": [],
    }

    related = {
        "id": related_id,
        "text": "Synthetic related fixture.",
        "source_id": "source:test:related",
        "work_id": "work:test",
        "citation_label": "Synthetic related citation",
        "language": "de",
        "text_kind": "editorial_summary",
        "review_status": "candidate",
        "is_verbatim": False,
        "is_editorial": True,
        "is_machine_generated": False,
    }

    paths = []
    for label in ("being", "becoming"):
        concept_id = f"concept:test:{label}"
        paths.append(
            {
                "seed_id": seed_id,
                "concept": {
                    "id": concept_id,
                    "canonical_label": label,
                    "concept_family": "dialectic",
                    "label_en": label,
                    "label_ru": None,
                    "label_de": None,
                },
                "seed_edge": {
                    "id": f"relation:test:seed:{label}",
                    "from_id": seed_id,
                    "to_id": concept_id,
                    "relation_type": "DISCUSSES",
                    "review_status": "candidate",
                    "extraction_method": "synthetic_fixture",
                    "confidence": None,
                },
                "related_edge": {
                    "id": f"relation:test:related:{label}",
                    "from_id": related_id,
                    "to_id": concept_id,
                    "relation_type": "DISCUSSES",
                    "review_status": "candidate",
                    "extraction_method": "synthetic_fixture",
                    "confidence": None,
                },
                "passage": related,
            }
        )

    payload = {
        "query": "Synthetic browser query",
        "mode": "retrieval_only",
        "semantic_count": 1,
        "graph_path_count": graph_path_count,
        "semantic_passages": [seed],
        "graph_context": paths[:graph_path_count],
    }

    search_ui.payload = payload
    page.goto("http://ui.test/search")

    page.locator("#query").fill("Synthetic browser query")
    page.locator("#limit").select_option("1")
    page.get_by_role("button", name="Search corpus", exact=True).click()

    semantic = page.locator('section[aria-labelledby="semantic-results-heading"]')
    graph = page.locator('section[aria-labelledby="graph-context-heading"]')

    expect(semantic).to_be_visible()
    expect(graph).to_be_visible()
    expect(semantic.locator(".result-card")).to_have_count(1)
    expect(semantic.locator(".score")).to_have_text("Vector similarity 0.875")
    expect(semantic.locator(".passage-text")).to_have_text("Synthetic semantic fixture.")

    expect(graph.locator(".score")).to_have_count(0)
    expect(graph).not_to_contain_text("Vector similarity 0.875")

    if graph_path_count:
        expect(graph.locator(".graph-card")).to_have_count(1)
        expect(graph.locator(".graph-paths > li")).to_have_count(2)
        expect(graph.locator(".empty-state")).to_have_count(0)
        expect(graph.locator(".passage-text")).to_have_text("Synthetic related fixture.")
        expect(graph.locator(".graph-summary")).to_have_text(
            "2 returned graph path(s); "
            "1 distinct related passage(s), "
            "1 not already shown in semantic matches. "
            "These are passage counts, not counts of distinct sources."
        )
        expect(graph.locator(".graph-origin")).to_have_text(
            "Additional graph-derived passage; not a separately ranked vector match."
        )
        expect(graph.locator(".graph-chain")).to_have_text(
            [
                "Synthetic semantic citation → DISCUSSES → being "
                "← DISCUSSES ← Synthetic related citation",
                "Synthetic semantic citation → DISCUSSES → becoming "
                "← DISCUSSES ← Synthetic related citation",
            ]
        )
    else:
        expect(graph.locator(".graph-card")).to_have_count(0)
        expect(graph.locator(".graph-summary")).to_have_count(0)
        expect(graph.locator(".empty-state")).to_have_text(
            "No graph paths were returned for this query. "
            "This does not establish that no relevant connections exist."
        )

    expect(page.locator("#status")).to_contain_text(
        "These are search matches, not a verified answer."
    )

    assert search_ui.query_requests == [
        {
            "q": "Synthetic browser query",
            "limit": 1,
            "graph_limit": 20,
        }
    ]


@pytest.mark.parametrize(
    ("status", "detail", "expected_message"),
    [
        (
            200,
            None,
            "No passages were returned for this query and the selected filters.",
        ),
        (
            429,
            "Synthetic rate-limit response.",
            "Search unavailable: Search is temporarily rate-limited. "
            "Please wait a moment and try again.",
        ),
        (
            503,
            "Query retrieval service is temporarily unavailable.",
            "Search unavailable: Query retrieval service is temporarily unavailable.",
        ),
    ],
    ids=["empty-results", "rate-limited", "service-unavailable"],
)
def test_search_handles_empty_results_and_api_errors(
    page: Page,
    search_ui,
    status: int,
    detail: str | None,
    expected_message: str,
) -> None:
    """Render empty results or API errors without JavaScript exceptions."""
    search_ui.status = status

    if status == 200:
        search_ui.payload = {
            "query": "Synthetic empty query",
            "mode": "retrieval_only",
            "semantic_count": 0,
            "graph_path_count": 0,
            "semantic_passages": [],
            "graph_context": [],
        }
    else:
        search_ui.payload = {"detail": detail}

    page.goto("http://ui.test/search")
    page.locator("#query").fill("Synthetic empty query")
    page.locator("#limit").select_option("1")
    page.get_by_role("button", name="Search corpus", exact=True).click()

    expect(page.locator("#status")).to_have_text(expected_message)
    expect(page.locator("#results .result-card")).to_have_count(0)

    if status == 200:
        semantic = page.locator('section[aria-labelledby="semantic-results-heading"]')
        graph = page.locator('section[aria-labelledby="graph-context-heading"]')

        expect(semantic).to_be_visible()
        expect(graph).to_be_visible()
        expect(semantic.locator(".empty-state")).to_contain_text(
            "This does not establish that the corpus contains no relevant passage."
        )
        expect(graph.locator(".empty-state")).to_have_text(
            "No graph paths were returned for this query. "
            "This does not establish that no relevant connections exist."
        )
        expect(page.locator("#status")).not_to_have_class("status error")
    else:
        expect(page.locator("#status")).to_have_class("status error")
        expect(page.locator("#results")).to_be_empty()

    assert search_ui.query_requests == [
        {
            "q": "Synthetic empty query",
            "limit": 1,
            "graph_limit": 20,
        }
    ]


@pytest.mark.parametrize(
    ("material_kind", "expected_provenance"),
    [
        ("", {}),
        ("primary", {"is_verbatim": True, "is_editorial": False}),
        ("editorial", {"is_verbatim": False, "is_editorial": True}),
    ],
    ids=["any-material", "primary-only", "editorial-only"],
)
def test_search_sends_selected_filters(
    page: Page,
    search_ui,
    material_kind: str,
    expected_provenance: dict[str, bool],
) -> None:
    """Send selected filters and a trimmed query in the POST body."""
    search_ui.payload = {
        "query": "Synthetic filtered query",
        "mode": "retrieval_only",
        "semantic_count": 0,
        "graph_path_count": 0,
        "semantic_passages": [],
        "graph_context": [],
    }

    page.goto("http://ui.test/search")

    expect(page.locator('#concept-family option[value="dialectic"]')).to_have_count(1)

    page.locator("#query").fill("  Synthetic filtered query  ")
    page.locator("#concept-family").select_option("dialectic")
    page.locator("#language").select_option("de")
    page.locator("#limit").select_option("3")
    page.locator(f'input[name="material_kind"][value="{material_kind}"]').check()

    page.get_by_role("button", name="Search corpus", exact=True).click()

    expect(page.locator("#status")).to_have_text(
        "No passages were returned for this query and the selected filters."
    )

    assert search_ui.query_requests == [
        {
            "q": "Synthetic filtered query",
            "limit": 3,
            "graph_limit": 20,
            "concept_family": "dialectic",
            "language": "de",
            **expected_provenance,
        }
    ]
