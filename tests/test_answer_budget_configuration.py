"""Validate the answer workflow execution budget setting."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from philosophy_influence_explorer.config import Settings


@pytest.fixture(autouse=True)
def isolate_answer_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANSWER_WORKFLOW_TIMEOUT_SECONDS", raising=False)


def test_answer_budget_default() -> None:
    settings = Settings(_env_file=None, neo4j_enabled=False)

    assert settings.answer_workflow_timeout_seconds == 120.0


@pytest.mark.parametrize(
    "value",
    [0, -1, float("inf"), float("-inf"), float("nan")],
)
def test_answer_budget_rejects_invalid_values(value: float) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            neo4j_enabled=False,
            answer_workflow_timeout_seconds=value,
        )


def test_answer_budget_loads_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANSWER_WORKFLOW_TIMEOUT_SECONDS", "12.5")

    settings = Settings(_env_file=None, neo4j_enabled=False)

    assert settings.answer_workflow_timeout_seconds == 12.5
