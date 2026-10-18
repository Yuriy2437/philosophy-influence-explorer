"""Tests for database health and graph summary endpoints."""

from collections.abc import Iterator
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.main import create_app


@pytest.fixture
def database_health_settings() -> Iterator[Settings]:
    """Use explicit test settings without changing runtime configuration."""
    settings = Settings(
        _env_file=None,
        app_env="development",
        api_v1_prefix="/api/v1",
        neo4j_enabled=True,
        neo4j_uri="bolt://neo4j.test:7687",
        neo4j_username="neo4j",
        neo4j_password="test-password",
        neo4j_database="neo4j",
        embedding_provider="not_configured",
        google_api_key=None,
    )

    with patch(
        "philosophy_influence_explorer.main.get_settings",
        return_value=settings,
    ):
        yield settings


def test_database_health_endpoint_verifies_connectivity(
    database_health_settings: Settings,
) -> None:
    """Database health should verify connectivity using test settings."""
    mocked_client = Mock()

    with patch(
        "philosophy_influence_explorer.main.Neo4jClient",
        return_value=mocked_client,
    ) as client_factory:
        with TestClient(create_app()) as client:
            response = client.get("/api/v1/health/database")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "neo4j"}
    client_factory.assert_called_once_with(database_health_settings)
    mocked_client.verify_connectivity.assert_called_once()
    mocked_client.close.assert_called_once()


def test_graph_summary_endpoint_returns_client_summary(
    database_health_settings: Settings,
) -> None:
    """Graph summary should return the mocked client's result."""
    mocked_client = Mock()
    mocked_client.get_graph_summary.return_value = {
        "total_nodes": 9,
        "total_relationships": 10,
    }

    with patch(
        "philosophy_influence_explorer.main.Neo4jClient",
        return_value=mocked_client,
    ) as client_factory:
        with TestClient(create_app()) as client:
            response = client.get("/api/v1/health/database/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total_nodes": 9,
        "total_relationships": 10,
    }
    client_factory.assert_called_once_with(database_health_settings)
    mocked_client.get_graph_summary.assert_called_once()
    mocked_client.close.assert_called_once()
