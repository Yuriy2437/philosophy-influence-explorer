"""Tests for the minimal browser search UI."""

from fastapi.testclient import TestClient

from philosophy_influence_explorer.main import create_app


def test_search_page_returns_html_shell_without_retrieval() -> None:
    """Loading the UI must not perform an Ollama or Neo4j search."""
    with TestClient(create_app()) as client:
        response = client.get("/search")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Concept-aware semantic search" in response.text
    assert 'id="search-form"' in response.text
    assert 'id="concept-family"' in response.text
    assert '<option value="">Any concept family</option>' in response.text

    # Concept families are loaded by JavaScript, not hardcoded in the HTML.
    assert 'value="ethics"' not in response.text
    assert 'value="political_philosophy"' not in response.text

    assert "/static/search.css" in response.text
    assert "/static/search.js" in response.text
    assert "/api/v1/passages/search" not in response.text


def test_search_static_assets_are_served() -> None:
    """The page CSS and JavaScript should be available from static routes."""
    with TestClient(create_app()) as client:
        css_response = client.get("/static/search.css")
        javascript_response = client.get("/static/search.js")

    assert css_response.status_code == 200
    assert "page-shell" in css_response.text
    assert javascript_response.status_code == 200
    assert "JSON.stringify(searchBody)" in javascript_response.text
    assert "method: 'POST'" in javascript_response.text
    assert "/api/v1/concepts/families" in javascript_response.text
    assert "passage.review_status" in javascript_response.text
    assert "temporarily rate-limited" in javascript_response.text


def test_search_page_explains_retrieval_limits_and_review_status() -> None:
    """The HTML distinguishes retrieval, similarity, and scholarly review."""
    with TestClient(create_app()) as client:
        response = client.get("/search")

    assert response.status_code == 200

    html = " ".join(response.text.split())

    assert 'aria-labelledby="search-guidance-heading"' in html
    assert 'id="similarity-guidance"' in html
    assert "About these results" in html
    assert "retrieves passages, not a generated or verified answer" in html
    assert "related to your query without answering it" in html
    assert "not probabilities of truth" in html
    assert "not completed scholarly verification" in html
    assert "Candidate records still require scholarly review" in html


def test_search_javascript_contains_cautious_result_messages() -> None:
    """The served script contains the agreed result and empty-state wording."""
    with TestClient(create_app()) as client:
        response = client.get("/static/search.js")

    assert response.status_code == 200

    script = response.text

    assert "retrieved passage" in script
    assert "These are search matches, not a verified answer." in script
    assert "No passages were returned for this query" in script
    assert "This does not establish that the corpus contains no relevant passage." in script
    assert "Vector similarity " in script
    assert "score.setAttribute('aria-describedby', 'similarity-guidance')" in script
    assert "No passages matched the selected filters." not in script
