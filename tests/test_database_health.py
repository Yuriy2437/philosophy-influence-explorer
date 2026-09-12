"""Tests for database health and graph summary endpoints."""

from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from philosophy_influence_explorer.main import create_app


def test_database_health_endpoint_verifies_connectivity() -> None:
    """Database health endpoint should call the Neo4j client verification method."""
    mocked_client = Mock()

    with patch(
        "philosophy_influence_explorer.main.Neo4jClient",
        return_value=mocked_client,
    ):
        with TestClient(create_app()) as client:
            response = client.get("/api/v1/health/database")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "neo4j"}
    mocked_client.verify_connectivity.assert_called_once()
    mocked_client.close.assert_called_once()


def test_graph_summary_endpoint_returns_client_summary() -> None:
    """Graph summary endpoint should return the graph client's result."""
    mocked_client = Mock()
    mocked_client.get_graph_summary.return_value = {
        "total_nodes": 9,
        "total_relationships": 10,
    }

    with patch(
        "philosophy_influence_explorer.main.Neo4jClient",
        return_value=mocked_client,
    ):
        with TestClient(create_app()) as client:
            response = client.get("/api/v1/health/database/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total_nodes": 9,
        "total_relationships": 10,
    }
    mocked_client.get_graph_summary.assert_called_once()
    mocked_client.close.assert_called_once()
