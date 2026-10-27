"""Test the evaluation CLI with fake services and temporary reports."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cli():
    path = ROOT / "scripts/evaluate_semantic_search.py"
    spec = importlib.util.spec_from_file_location("evaluation_cli_under_test", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_services(cli, monkeypatch, tmp_path):
    output = tmp_path / "report.json"
    state = SimpleNamespace(
        closed=False,
        verified=False,
        client_created=False,
        calls=[],
        fail_query=False,
        fail_connectivity=False,
    )

    class FakeClient:
        def __init__(self, settings):
            state.client_created = True

        def verify_connectivity(self):
            state.verified = True
            if state.fail_connectivity:
                raise RuntimeError("Synthetic connectivity failure")

        def close(self):
            state.closed = True

    class FakeRetriever:
        def __init__(self, *, client, provider):
            pass

        def search(self, query_text, *, limit, filters):
            state.calls.append(
                {
                    "query": query_text,
                    "limit": limit,
                    "filters": filters,
                }
            )
            if state.fail_query and len(state.calls) == 1:
                raise RuntimeError("Synthetic query failure")
            return []

    args = SimpleNamespace(
        suite=ROOT / "data/evaluation/semantic-search-v1.json",
        judgments=ROOT / "data/evaluation/semantic-search-judgments-v1.json",
        output=output,
    )
    provider = SimpleNamespace(
        model_info=SimpleNamespace(
            provider="gemini",
            model="gemini-embedding-001",
            dimensions=768,
        )
    )

    monkeypatch.setattr(cli, "parse_args", lambda: args)
    monkeypatch.setattr(
        cli,
        "Settings",
        lambda: SimpleNamespace(neo4j_enabled=True),
    )
    monkeypatch.setattr(cli, "create_embedding_provider", lambda settings: provider)
    monkeypatch.setattr(cli, "Neo4jClient", FakeClient)
    monkeypatch.setattr(cli, "PassageRetriever", FakeRetriever)

    return SimpleNamespace(
        output=output,
        state=state,
        provider=provider,
    )


def test_cli_writes_report_and_closes_client(cli, fake_services):
    assert cli.main() == 0

    report = json.loads(fake_services.output.read_text(encoding="utf-8"))
    assert report["summary"] == {
        "case_count": 12,
        "query_error_count": 0,
        "filter_failure_case_count": 0,
    }
    assert report["embedding_configuration_matches_historical"] is True
    assert report["current_corpus_snapshot_verified"] is False
    assert len(report["cases"]) == 12
    assert all(case["returned_count"] == 0 for case in report["cases"])
    assert fake_services.state.verified is True
    assert fake_services.state.closed is True

    assert len(fake_services.state.calls) == 12
    for call in fake_services.state.calls:
        assert call["limit"] == 3
        assert call["filters"].is_verbatim is True
        assert call["filters"].is_editorial is False


def test_query_failure_is_saved_and_remaining_cases_run(cli, fake_services):
    fake_services.state.fail_query = True

    assert cli.main() == 1

    report = json.loads(fake_services.output.read_text(encoding="utf-8"))
    assert report["summary"]["query_error_count"] == 1
    assert report["cases"][0]["status"] == "error"
    assert report["cases"][0]["error_type"] == "RuntimeError"
    assert report["cases"][0]["returned_count"] is None
    assert report["cases"][1]["status"] == "success"
    assert len(fake_services.state.calls) == 12
    assert fake_services.state.closed is True
    assert "Synthetic query failure" not in fake_services.output.read_text(encoding="utf-8")


def test_existing_report_is_not_overwritten(cli, fake_services):
    fake_services.output.write_text("original", encoding="utf-8")

    with pytest.raises(FileExistsError):
        cli.main()

    assert fake_services.output.read_text(encoding="utf-8") == "original"
    assert fake_services.state.client_created is False


def test_disabled_database_is_rejected(cli, fake_services, monkeypatch):
    monkeypatch.setattr(
        cli,
        "Settings",
        lambda: SimpleNamespace(neo4j_enabled=False),
    )

    with pytest.raises(ValueError, match="NEO4J_ENABLED"):
        cli.main()

    assert fake_services.state.client_created is False
    assert not fake_services.output.exists()


def test_connectivity_failure_closes_client(cli, fake_services):
    fake_services.state.fail_connectivity = True

    with pytest.raises(RuntimeError, match="connectivity"):
        cli.main()

    assert fake_services.state.closed is True
    assert fake_services.state.calls == []
    assert not fake_services.output.exists()


def test_different_embedding_configuration_is_marked(cli, fake_services):
    fake_services.provider.model_info.model = "synthetic-other-model"

    assert cli.main() == 0

    report = json.loads(fake_services.output.read_text(encoding="utf-8"))
    assert report["embedding_configuration_matches_historical"] is False
