"""Test Neo4j connection settings without a database connection."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.graph import neo4j_client as client_module


@pytest.fixture(autouse=True)
def isolate_connection_settings(monkeypatch):
    for name in (
        "NEO4J_CONNECTION_TIMEOUT_SECONDS",
        "NEO4J_CONNECTION_ACQUISITION_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_connection_timeout_defaults() -> None:
    settings = Settings(
        _env_file=None,
        neo4j_enabled=False,
    )

    assert settings.neo4j_connection_timeout_seconds == 10.0
    assert settings.neo4j_connection_acquisition_timeout_seconds == 20.0


@pytest.mark.parametrize(
    "field",
    [
        "neo4j_connection_timeout_seconds",
        "neo4j_connection_acquisition_timeout_seconds",
    ],
)
@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan")])
def test_invalid_connection_timeouts_are_rejected(
    field: str,
    value: float,
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            neo4j_enabled=False,
            **{field: value},
        )


def test_client_passes_connection_timeouts_to_driver(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        neo4j_enabled=True,
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="test-user",
        neo4j_password="test-password",
        neo4j_database="test-database",
        neo4j_connection_timeout_seconds=7.0,
        neo4j_connection_acquisition_timeout_seconds=15.0,
    )
    driver = Mock()
    driver_factory = Mock(return_value=driver)

    monkeypatch.setattr(
        client_module.GraphDatabase,
        "driver",
        driver_factory,
    )

    client = client_module.Neo4jClient(settings)
    try:
        driver_factory.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("test-user", "test-password"),
            connection_timeout=7.0,
            connection_acquisition_timeout=15.0,
        )
        driver.verify_connectivity.assert_not_called()
    finally:
        client.close()

    driver.close.assert_called_once_with()


def test_connection_timeouts_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("NEO4J_CONNECTION_TIMEOUT_SECONDS", "8.5")
    monkeypatch.setenv(
        "NEO4J_CONNECTION_ACQUISITION_TIMEOUT_SECONDS",
        "18",
    )

    settings = Settings(
        _env_file=None,
        neo4j_enabled=False,
    )

    assert settings.neo4j_connection_timeout_seconds == 8.5
    assert settings.neo4j_connection_acquisition_timeout_seconds == 18.0


def test_installed_driver_accepts_connection_configuration_without_network(
    monkeypatch,
) -> None:
    import socket

    def deny_network(*args, **kwargs):
        raise AssertionError("Unexpected network operation.")

    monkeypatch.setattr(socket, "getaddrinfo", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)

    settings = Settings(
        _env_file=None,
        neo4j_enabled=True,
        neo4j_uri="bolt://127.0.0.1:7687",
        neo4j_username="test-user",
        neo4j_password="test-password",
        neo4j_database="test-database",
        neo4j_connection_timeout_seconds=7.0,
        neo4j_connection_acquisition_timeout_seconds=15.0,
    )

    client = client_module.Neo4jClient(settings)
    client.close()
