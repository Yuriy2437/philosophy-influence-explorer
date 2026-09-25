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
    assert "URLSearchParams" in javascript_response.text
