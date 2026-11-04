"""Exercise the fixed-evidence runner without model or database calls."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import create_autospec

import pytest

from philosophy_influence_explorer.evaluation.answer_dataset import (
    AnswerSuite,
    load_answer_evaluation,
)
from philosophy_influence_explorer.evaluation.answer_runner import (
    run_answer_evaluation,
)
from philosophy_influence_explorer.generation.base import AnswerGenerator
from philosophy_influence_explorer.generation.contracts import (
    AnswerClaim,
    GroundedAnswer,
)
from philosophy_influence_explorer.ingestion.validators import (
    validate_curated_corpus,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def evaluation_data():
    corpus_dir = ROOT / "data" / "curated"
    suite = load_answer_evaluation(
        ROOT / "data" / "evaluation" / "answer-quality-v1.json",
        corpus_dir,
        ROOT / "data" / "evaluation" / "semantic-search-v1.json",
    )
    passages = validate_curated_corpus(corpus_dir)["passages"]
    return suite, passages


def insufficient_answer() -> GroundedAnswer:
    return GroundedAnswer(
        status="insufficient_evidence",
        claims=[],
        limitations=["Synthetic limitation, not a scholarly assessment."],
    )


def single_case_suite(suite: AnswerSuite) -> AnswerSuite:
    data = suite.model_dump()
    data["cases"] = data["cases"][:1]
    return AnswerSuite.model_validate(data)


def test_runs_all_cases_once_and_preserves_inputs(evaluation_data) -> None:
    suite, passages = evaluation_data
    before_suite = suite.model_dump()
    before_passages = deepcopy(passages)
    generator = create_autospec(AnswerGenerator, instance=True)
    generator.generate.side_effect = lambda **kwargs: insufficient_answer()

    report = run_answer_evaluation(suite, passages, generator)

    assert len(report["results"]) == 8
    assert generator.generate.call_count == 8
    assert suite.model_dump() == before_suite
    assert passages == before_passages

    for case, result, call in zip(
        suite.cases,
        report["results"],
        generator.generate.call_args_list,
        strict=True,
    ):
        assert call.args == ()
        assert call.kwargs["query_text"] == case.query
        assert [
            passage.id for passage in call.kwargs["evidence"].passages
        ] == case.evidence_passage_ids
        assert result["case"] == case.model_dump(mode="json")
        assert result["checks"] == {
            "structure_valid": True,
            "references_valid": True,
            "status_allowed": ("insufficient_evidence" in case.allowed_answer_statuses),
        }
        assert result["error"] is None
        assert result["answer"]["status"] == "insufficient_evidence"
        assert result["generation_duration_seconds"] >= 0
        assert result["manual_review"] == {"verdict": None, "notes": None}

    decoded = json.loads(json.dumps(report, ensure_ascii=False))
    assert len(decoded["results"]) == 8


def test_snapshot_and_hash_match_supplied_packet(evaluation_data) -> None:
    suite, passages = evaluation_data
    suite = single_case_suite(suite)
    generator = create_autospec(AnswerGenerator, instance=True)
    generator.generate.return_value = insufficient_answer()

    report = run_answer_evaluation(suite, passages, generator)
    result = report["results"][0]
    snapshot = result["evidence"]

    assert snapshot["semantic_passage_ids"] == ()
    assert snapshot["additional_graph_passage_ids"] == ()
    assert [item["id"] for item in snapshot["passages"]] == (suite.cases[0].evidence_passage_ids)

    by_id = {passage.id: passage for passage in passages}
    for item in snapshot["passages"]:
        record = by_id[item["id"]]
        assert item["text"] == record.text
        assert item["review_status"] == record.review_status.value
        assert item["text_kind"] == record.text_kind.value
        assert item["is_verbatim"] == record.is_verbatim

    encoded = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    assert result["evidence_sha256"] == hashlib.sha256(encoded).hexdigest()

    second = run_answer_evaluation(suite, passages, generator)
    assert second["results"][0]["evidence_sha256"] == result["evidence_sha256"]


def test_generation_error_is_recorded_without_retry(evaluation_data) -> None:
    suite, passages = evaluation_data
    generator = create_autospec(AnswerGenerator, instance=True)
    generator.generate.side_effect = [
        RuntimeError("Synthetic generator failure"),
        *[insufficient_answer() for _ in suite.cases[1:]],
    ]

    report = run_answer_evaluation(suite, passages, generator)
    first = report["results"][0]

    assert generator.generate.call_count == len(suite.cases)
    assert first["error"] == {
        "stage": "generation",
        "type": "RuntimeError",
        "message": "Synthetic generator failure",
    }
    assert first["answer"] is None
    assert first["draft_answer"] is None
    assert all(value is None for value in first["checks"].values())
    assert report["results"][1]["error"] is None


def test_wrong_return_type_is_structure_error(evaluation_data) -> None:
    suite, passages = evaluation_data
    generator = create_autospec(AnswerGenerator, instance=True)
    generator.generate.return_value = {"status": "insufficient_evidence"}

    report = run_answer_evaluation(single_case_suite(suite), passages, generator)
    result = report["results"][0]

    assert result["error"]["stage"] == "structure"
    assert result["checks"]["structure_valid"] is False
    assert result["checks"]["references_valid"] is None
    assert result["answer"] is None
    generator.generate.assert_called_once()


def test_revalidates_mutated_model(evaluation_data) -> None:
    suite, passages = evaluation_data
    draft = insufficient_answer()
    draft.limitations.clear()
    generator = create_autospec(AnswerGenerator, instance=True)
    generator.generate.return_value = draft

    report = run_answer_evaluation(single_case_suite(suite), passages, generator)
    result = report["results"][0]

    assert result["error"]["stage"] == "structure"
    assert result["checks"]["structure_valid"] is False
    assert result["draft_answer"]["limitations"] == []
    assert result["answer"] is None


def test_unknown_reference_keeps_draft_but_not_answer(evaluation_data) -> None:
    suite, passages = evaluation_data
    generator = create_autospec(AnswerGenerator, instance=True)
    generator.generate.return_value = GroundedAnswer(
        status="answered",
        claims=[
            AnswerClaim(
                text="Synthetic assertion.",
                passage_ids=["passage:not-supplied"],
            )
        ],
        limitations=[],
    )

    report = run_answer_evaluation(single_case_suite(suite), passages, generator)
    result = report["results"][0]

    assert result["checks"]["structure_valid"] is True
    assert result["checks"]["references_valid"] is False
    assert result["error"]["stage"] == "references"
    assert result["draft_answer"]["claims"][0]["passage_ids"] == ["passage:not-supplied"]
    assert result["answer"] is None


def test_disallowed_status_is_not_execution_error(evaluation_data) -> None:
    suite, passages = evaluation_data
    data = single_case_suite(suite).model_dump()
    data["cases"][0]["allowed_answer_statuses"] = ["answered"]
    suite = AnswerSuite.model_validate(data)
    generator = create_autospec(AnswerGenerator, instance=True)
    generator.generate.return_value = insufficient_answer()

    result = run_answer_evaluation(suite, passages, generator)["results"][0]

    assert result["checks"]["status_allowed"] is False
    assert result["checks"]["structure_valid"] is True
    assert result["checks"]["references_valid"] is True
    assert result["error"] is None
    assert result["answer"]["status"] == "insufficient_evidence"


def test_invalid_later_evidence_prevents_all_generator_calls(
    evaluation_data,
) -> None:
    suite, passages = evaluation_data
    data = suite.model_dump()
    data["cases"][-1]["evidence_passage_ids"] = ["passage:missing"]
    suite = AnswerSuite.model_validate(data)
    generator = create_autospec(AnswerGenerator, instance=True)

    with pytest.raises(ValueError, match="Unknown evidence passage"):
        run_answer_evaluation(suite, passages, generator)

    generator.generate.assert_not_called()


def test_keyboard_interrupt_is_not_swallowed(evaluation_data) -> None:
    suite, passages = evaluation_data
    generator = create_autospec(AnswerGenerator, instance=True)
    generator.generate.side_effect = KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_answer_evaluation(single_case_suite(suite), passages, generator)

    generator.generate.assert_called_once()
