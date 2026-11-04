"""Test explicitly gated Gemini evaluation using fake HTTP only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

from philosophy_influence_explorer.evaluation.answer_cli import (
    main,
    run_gemini_case,
)
from philosophy_influence_explorer.generation.gemini import SYSTEM_INSTRUCTION

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "answer-negative-n3"
TEST_KEY = "synthetic-evaluation-key"


@pytest.fixture
def fake_post(monkeypatch: pytest.MonkeyPatch) -> Mock:
    answer = {
        "status": "insufficient_evidence",
        "claims": [],
        "limitations": ["The supplied passages contain no entanglement experiments."],
    }
    payload = {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(answer)}]},
            }
        ]
    }
    post = Mock(
        return_value=httpx.Response(
            200,
            json=payload,
            request=httpx.Request("POST", "https://example.test/generate"),
        )
    )
    monkeypatch.setattr(httpx, "post", post)
    monkeypatch.setenv("GOOGLE_API_KEY", TEST_KEY)
    return post


def parameters(tmp_path: Path) -> dict:
    return {
        "root": ROOT,
        "case_id": CASE_ID,
        "model": "test-model",
        "destination": tmp_path / "report.json",
        "allow_network": True,
    }


def test_runs_one_case_and_saves_metadata(
    tmp_path: Path,
    fake_post: Mock,
) -> None:
    args = parameters(tmp_path)

    report = run_gemini_case(**args)

    fake_post.assert_called_once()
    request = fake_post.call_args
    assert request.kwargs["headers"] == {"x-goog-api-key": TEST_KEY}
    assert request.args[0].endswith("models/test-model:generateContent")

    sent = json.loads(request.kwargs["json"]["contents"][0]["parts"][0]["text"])
    assert len(sent["passages"]) == 3
    assert sent["semantic_passage_ids"] == []
    assert sent["additional_graph_passage_ids"] == []
    assert "required_points" not in sent
    assert "allowed_answer_statuses" not in sent

    loaded = json.loads(args["destination"].read_text(encoding="utf-8"))
    assert loaded == json.loads(json.dumps(report))
    assert len(loaded["results"]) == 1
    assert loaded["results"][0]["case"]["id"] == CASE_ID
    assert loaded["results"][0]["manual_review"]["verdict"] is None
    assert loaded["execution"]["requested_model"] == "test-model"
    assert loaded["execution"]["system_instruction_sha256"] == (
        hashlib.sha256(SYSTEM_INSTRUCTION.encode("utf-8")).hexdigest()
    )
    assert TEST_KEY not in args["destination"].read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "overrides",
    [
        {"allow_network": False},
        {"case_id": "answer-missing"},
        {"model": "models/test-model"},
        {"timeout_seconds": 0},
        {"max_input_bytes": 0},
    ],
)
def test_invalid_setup_does_not_call_http(
    tmp_path: Path,
    fake_post: Mock,
    overrides: dict,
) -> None:
    args = parameters(tmp_path)
    args.update(overrides)

    with pytest.raises(ValueError):
        run_gemini_case(**args)

    fake_post.assert_not_called()
    assert not args["destination"].exists()


def test_missing_key_does_not_call_http(
    tmp_path: Path,
    fake_post: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        run_gemini_case(**parameters(tmp_path))

    fake_post.assert_not_called()


def test_existing_report_prevents_provider_call(
    tmp_path: Path,
    fake_post: Mock,
) -> None:
    args = parameters(tmp_path)
    args["destination"].write_text("original", encoding="utf-8")

    with pytest.raises(FileExistsError):
        run_gemini_case(**args)

    fake_post.assert_not_called()
    assert args["destination"].read_text(encoding="utf-8") == "original"


def test_missing_parent_prevents_provider_call(
    tmp_path: Path,
    fake_post: Mock,
) -> None:
    args = parameters(tmp_path)
    args["destination"] = tmp_path / "missing" / "report.json"

    with pytest.raises(FileNotFoundError):
        run_gemini_case(**args)

    fake_post.assert_not_called()


def test_http_failure_is_saved_without_retry(
    tmp_path: Path,
    fake_post: Mock,
) -> None:
    fake_post.return_value = httpx.Response(
        429,
        json={"error": {"message": "private-response-marker"}},
        request=httpx.Request("POST", "https://example.test/generate"),
    )
    args = parameters(tmp_path)

    report = run_gemini_case(**args)

    fake_post.assert_called_once()
    result = report["results"][0]
    assert result["error"]["stage"] == "generation"
    assert "HTTP 429" in result["error"]["message"]
    assert result["answer"] is None
    saved = args["destination"].read_text(encoding="utf-8")
    assert TEST_KEY not in saved
    assert "private-response-marker" not in saved


def test_cli_success_requires_manual_review(
    tmp_path: Path,
    fake_post: Mock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "--root",
            str(ROOT),
            "--case-id",
            CASE_ID,
            "--model",
            "test-model",
            "--output",
            str(tmp_path / "report.json"),
            "--allow-network",
        ]
    )

    assert code == 0
    assert "Manual review is pending" in capsys.readouterr().out
    fake_post.assert_called_once()


def test_cli_without_gate_exits_before_http(
    tmp_path: Path,
    fake_post: Mock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as caught:
        main(
            [
                "--root",
                str(ROOT),
                "--case-id",
                CASE_ID,
                "--model",
                "test-model",
                "--output",
                str(tmp_path / "report.json"),
            ]
        )

    assert caught.value.code == 2
    assert TEST_KEY not in capsys.readouterr().err
    fake_post.assert_not_called()
