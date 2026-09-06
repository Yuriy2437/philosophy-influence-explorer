"""Tests for basic API availability."""

from fastapi.testclient import TestClient

from philosophy_influence_explorer.main import create_app


def test_root_returns_service_metadata() -> None:
    """The root endpoint should expose service navigation metadata."""
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["service"] == "Philosophy Influence Explorer API"
    assert response.json()["docs"] == "/docs"
    assert response.json()["health"] == "/api/v1/health"


def test_health_endpoint_returns_expected_contract() -> None:
    """The health endpoint should return the documented stable shape."""
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Philosophy Influence Explorer API",
        "environment": "development",
        "version": "0.1.0",
    }
