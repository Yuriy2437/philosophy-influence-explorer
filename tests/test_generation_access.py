"""Test generation settings and access without external services."""

from __future__ import annotations

from typing import Annotated
from unittest.mock import Mock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from philosophy_influence_explorer.api.generation_access import (
    require_generation_access,
)
from philosophy_influence_explorer.config import Settings, get_settings


@pytest.fixture(autouse=True)
def isolate_generation_environment(monkeypatch):
    for name in (
        "GENERATION_ENABLED",
        "GENERATION_ACCESS_TOKEN",
        "GENERATION_MODEL",
        "GENERATION_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


def make_settings(**overrides) -> Settings:
    return Settings(
        _env_file=None,
        neo4j_enabled=False,
        **overrides,
    )


def make_client(settings: Settings, service_factory: Mock) -> TestClient:
    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings

    @app.post("/protected")
    def protected(
        approved: Annotated[Settings, Depends(require_generation_access)],
    ) -> dict[str, bool]:
        service_factory()
        return {"enabled": approved.generation_enabled}

    return TestClient(app)


def test_generation_is_disabled_by_default() -> None:
    settings = make_settings()

    assert settings.generation_enabled is False
    assert settings.generation_access_token is None
    assert settings.generation_model == "gemini-3.5-flash-lite"
    assert settings.generation_timeout_seconds == 60.0


@pytest.mark.parametrize(
    "overrides",
    [
        {"generation_model": ""},
        {"generation_model": "models/test-model"},
        {"generation_model": "../test-model"},
        {"generation_timeout_seconds": 0},
        {"generation_timeout_seconds": -1},
        {"generation_timeout_seconds": float("inf")},
        {"generation_timeout_seconds": float("nan")},
    ],
)
def test_invalid_generation_settings_are_rejected(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        make_settings(**overrides)


def test_disabled_generation_prevents_service_creation() -> None:
    factory = Mock()
    settings = make_settings(
        generation_enabled=False,
        generation_access_token="operator-test-token",
    )

    with make_client(settings, factory) as client:
        response = client.post(
            "/protected",
            headers={"Authorization": "Bearer operator-test-token"},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Answer generation is unavailable."
    }
    factory.assert_not_called()


@pytest.mark.parametrize("token", [None, "", "   "])
def test_missing_server_token_prevents_service_creation(token) -> None:
    factory = Mock()
    settings = make_settings(
        generation_enabled=True,
        generation_access_token=token,
    )

    with make_client(settings, factory) as client:
        response = client.post(
            "/protected",
            headers={"Authorization": "Bearer operator-test-token"},
        )

    assert response.status_code == 503
    factory.assert_not_called()


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer wrong-test-token"},
        {"Authorization": "Basic operator-test-token"},
        {"Authorization": "Bearer"},
    ],
)
def test_invalid_access_prevents_service_creation(headers: dict) -> None:
    factory = Mock()
    settings = make_settings(
        generation_enabled=True,
        generation_access_token="operator-test-token",
    )

    with make_client(settings, factory) as client:
        response = client.post("/protected", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Generation access denied."}
    assert "operator-test-token" not in response.text
    factory.assert_not_called()


def test_valid_access_allows_service_creation_once() -> None:
    factory = Mock()
    settings = make_settings(
        generation_enabled=True,
        generation_access_token="operator-test-token",
    )

    with make_client(settings, factory) as client:
        response = client.post(
            "/protected",
            headers={"Authorization": "Bearer operator-test-token"},
        )

    assert response.status_code == 200
    assert response.json() == {"enabled": True}
    factory.assert_called_once_with()


def test_access_token_is_hidden_in_settings_repr() -> None:
    settings = make_settings(
        generation_access_token="operator-test-token",
    )

    assert "operator-test-token" not in repr(settings)


def test_generation_settings_can_be_loaded_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("GENERATION_ENABLED", "true")
    monkeypatch.setenv("GENERATION_ACCESS_TOKEN", "environment-test-token")
    monkeypatch.setenv("GENERATION_MODEL", "test-model")
    monkeypatch.setenv("GENERATION_TIMEOUT_SECONDS", "12.5")

    settings = make_settings()

    assert settings.generation_enabled is True
    assert settings.generation_access_token is not None
    assert (
        settings.generation_access_token.get_secret_value()
        == "environment-test-token"
    )
    assert settings.generation_model == "test-model"
    assert settings.generation_timeout_seconds == 12.5
