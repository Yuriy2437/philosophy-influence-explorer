"""Tests for running the application without Neo4j."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from philosophy_influence_explorer.config import Settings, get_settings
from philosophy_influence_explorer.main import create_app


def test_disabled_database_does_not_require_password() -> None:
    settings = Settings(
        _env_file=None,
        neo4j_enabled=False,
        neo4j_password=None,
    )

    assert settings.neo4j_password is None


def test_enabled_database_requires_password() -> None:
    with pytest.raises(ValidationError, match="NEO4J_PASSWORD"):
        Settings(
            _env_file=None,
            neo4j_enabled=True,
            neo4j_password=None,
        )


def test_application_runs_without_database(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        neo4j_enabled=False,
        neo4j_password=None,
        app_env="production",
    )
    monkeypatch.setattr(
        "philosophy_influence_explorer.main.get_settings",
        lambda: settings,
    )

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings

    with TestClient(app) as client:
        assert app.state.neo4j_client is None
        assert client.get("/").status_code == 200
        assert client.get("/docs").status_code == 200
        assert client.get("/search").status_code == 200
        assert client.get("/static/search.css").status_code == 200
        assert client.get("/static/search.js").status_code == 200
        assert client.get("/api/v1/concepts/families").status_code == 503
