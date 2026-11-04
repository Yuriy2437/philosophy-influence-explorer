"""Test report persistence without external services."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import create_autospec

import pytest

from philosophy_influence_explorer.evaluation.answer_dataset import (
    load_answer_evaluation,
)
from philosophy_influence_explorer.evaluation.answer_report import (
    save_answer_report,
)
from philosophy_influence_explorer.evaluation.answer_runner import (
    run_answer_evaluation,
)
from philosophy_influence_explorer.generation.base import AnswerGenerator
from philosophy_influence_explorer.generation.contracts import GroundedAnswer
from philosophy_influence_explorer.ingestion.validators import (
    validate_curated_corpus,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def runner_report() -> dict:
    corpus_dir = ROOT / "data" / "curated"
    suite = load_answer_evaluation(
        ROOT / "data" / "evaluation" / "answer-quality-v1.json",
        corpus_dir,
        ROOT / "data" / "evaluation" / "semantic-search-v1.json",
    )
    passages = validate_curated_corpus(corpus_dir)["passages"]

    generator = create_autospec(AnswerGenerator, instance=True)
    generator.generate.side_effect = [
        RuntimeError("Синтетическая ошибка генерации"),
        *[
            GroundedAnswer(
                status="insufficient_evidence",
                claims=[],
                limitations=["Недостаточно данных: Sein, Nichts, Werden."],
            )
            for _ in suite.cases[1:]
        ],
    ]

    return run_answer_evaluation(suite, passages, generator)


def test_saves_complete_runner_report(
    tmp_path: Path,
    runner_report: dict,
) -> None:
    destination = tmp_path / "answer-report.json"
    before = deepcopy(runner_report)

    save_answer_report(runner_report, destination)

    raw = destination.read_bytes()
    loaded = json.loads(raw.decode("utf-8"))
    expected = json.loads(json.dumps(runner_report, ensure_ascii=False, allow_nan=False))

    assert loaded == expected
    assert runner_report == before
    assert len(loaded["results"]) == 8
    assert loaded["results"][0]["error"]["stage"] == "generation"
    assert loaded["results"][0]["answer"] is None
    assert loaded["results"][1]["answer"]["status"] == ("insufficient_evidence")

    for result in loaded["results"]:
        assert result["case"]["evidence_passage_ids"]
        assert result["evidence"]["passages"]
        assert len(result["evidence_sha256"]) == 64
        assert result["manual_review"] == {
            "verdict": None,
            "notes": None,
        }

    assert "Синтетическая ошибка генерации" in raw.decode("utf-8")
    assert "Недостаточно данных" in raw.decode("utf-8")
    assert b"\\u0421" not in raw
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.endswith(b"\n")
    assert b"\r\n" not in raw


def test_refuses_to_overwrite_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "answer-report.json"
    original = b"Existing report must remain unchanged.\n"
    destination.write_bytes(original)

    with pytest.raises(FileExistsError):
        save_answer_report({"replacement": True}, destination)

    assert destination.read_bytes() == original


def test_refuses_to_overwrite_empty_file(tmp_path: Path) -> None:
    destination = tmp_path / "answer-report.json"
    destination.touch()

    with pytest.raises(FileExistsError):
        save_answer_report({"replacement": True}, destination)

    assert destination.read_bytes() == b""


def test_serialization_failure_does_not_create_file(tmp_path: Path) -> None:
    destination = tmp_path / "answer-report.json"

    with pytest.raises(TypeError):
        save_answer_report({"unsupported": object()}, destination)

    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), float("-inf")],
)
def test_rejects_nonfinite_numbers_before_creating_file(
    tmp_path: Path,
    value: float,
) -> None:
    destination = tmp_path / "answer-report.json"

    with pytest.raises(ValueError):
        save_answer_report({"duration": value}, destination)

    assert not destination.exists()


def test_does_not_create_parent_directories(tmp_path: Path) -> None:
    parent = tmp_path / "missing"
    destination = parent / "answer-report.json"

    with pytest.raises(FileNotFoundError):
        save_answer_report({"results": []}, destination)

    assert not parent.exists()


def test_serialization_error_preserves_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "answer-report.json"
    original = b"Original report.\n"
    destination.write_bytes(original)

    with pytest.raises(TypeError):
        save_answer_report({"unsupported": object()}, destination)

    assert destination.read_bytes() == original
