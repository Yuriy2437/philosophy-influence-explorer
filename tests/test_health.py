"""Tests for basic API availability."""

from fastapi.testclient import TestClient

from philosophy_influence_explorer.main import create_app


def test_root_returns_service_metadata() -> None:
    """The root endpoint should expose service navigation metadata."""
    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["service"] == "Philosophy Influence Explorer API"
    assert response.json()["docs"] == "/docs"
    assert response.json()["health"] == "/api/v1/health"
    assert response.json()["database_health"] == "/api/v1/health/database"
    assert response.json()["graph_summary"] == "/api/v1/health/database/summary"


def test_health_endpoint_returns_expected_contract() -> None:
    """The application health endpoint should return the documented stable shape."""
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Philosophy Influence Explorer API",
        "environment": "development",
        "version": "0.1.0",
    }
