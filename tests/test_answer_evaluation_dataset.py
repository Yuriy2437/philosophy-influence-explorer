"""Validate answer evaluation data without database or model calls."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from philosophy_influence_explorer.evaluation.answer_dataset import (
    AnswerSuite,
    load_answer_evaluation,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "data" / "curated"
SEARCH_SUITE = ROOT / "data" / "evaluation" / "semantic-search-v1.json"

QUERY = "How is becoming related to being and nothing?"
PASSAGE_ID = "passage:hegel:wl:being:de"


def payload() -> dict:
    return {
        "schema_version": 1,
        "suite_id": "answer-quality-v1",
        "mode": "fixed_evidence",
        "description": "Synthetic loader test, not an approved quality rubric.",
        "cases": [
            {
                "id": "answer-q5",
                "source_case_id": "q5",
                "query": QUERY,
                "evidence_passage_ids": [PASSAGE_ID],
                "allowed_answer_statuses": ["answered"],
                "required_points": ["Synthetic review criterion."],
                "required_limitations": [],
                "forbidden_inferences": ["Synthetic prohibited inference."],
                "rationale": "Synthetic fixture for loader validation.",
            }
        ],
    }


def write_suite(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "answer-suite.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_loads_case_against_real_local_corpus(tmp_path: Path) -> None:
    path = write_suite(tmp_path, payload())

    suite = load_answer_evaluation(path, CORPUS_DIR, SEARCH_SUITE)

    assert suite.mode == "fixed_evidence"
    assert suite.cases[0].evidence_passage_ids == [PASSAGE_ID]
    assert suite.cases[0].query == QUERY


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "   "),
        ("query", " " + QUERY),
        ("evidence_passage_ids", []),
        ("evidence_passage_ids", [PASSAGE_ID, PASSAGE_ID]),
        ("allowed_answer_statuses", []),
        ("allowed_answer_statuses", ["unknown"]),
        ("allowed_answer_statuses", ["answered", "answered"]),
        ("required_points", ["   "]),
        ("required_limitations", [123]),
        ("rationale", 123),
    ],
)
def test_rejects_invalid_case_fields(field: str, value: object) -> None:
    data = payload()
    data["cases"][0][field] = value

    with pytest.raises(ValidationError):
        AnswerSuite.model_validate(data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", 2),
        ("suite_id", "wrong-suite"),
        ("mode", "live_workflow"),
        ("description", "   "),
        ("cases", []),
    ],
)
def test_rejects_invalid_suite_fields(field: str, value: object) -> None:
    data = payload()
    data[field] = value

    with pytest.raises(ValidationError):
        AnswerSuite.model_validate(data)


def test_rejects_extra_case_field() -> None:
    data = payload()
    data["cases"][0]["automatic_scholarly_approval"] = True

    with pytest.raises(ValidationError):
        AnswerSuite.model_validate(data)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "evidence_passage_ids",
            ["passage:missing"],
            "Unknown evidence passage",
        ),
        ("source_case_id", "missing", "Unknown source case"),
        ("query", "A different question?", "Source query mismatch"),
    ],
)
def test_rejects_cross_reference_errors(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    data = payload()
    data["cases"][0][field] = value
    path = write_suite(tmp_path, data)

    with pytest.raises(ValueError, match=message):
        load_answer_evaluation(path, CORPUS_DIR, SEARCH_SUITE)


def test_rejects_duplicate_answer_case_id(tmp_path: Path) -> None:
    data = payload()
    data["cases"].append(deepcopy(data["cases"][0]))
    path = write_suite(tmp_path, data)

    with pytest.raises(ValueError, match="Duplicate answer case ID"):
        load_answer_evaluation(path, CORPUS_DIR, SEARCH_SUITE)


def test_rejects_duplicate_source_case_id(tmp_path: Path) -> None:
    data = payload()
    second = deepcopy(data["cases"][0])
    second["id"] = "another-answer-case"
    data["cases"].append(second)
    path = write_suite(tmp_path, data)

    with pytest.raises(ValueError, match="Duplicate source case ID"):
        load_answer_evaluation(path, CORPUS_DIR, SEARCH_SUITE)


def test_repository_answer_suite_loads_with_expected_cases() -> None:
    suite = load_answer_evaluation(
        ROOT / "data" / "evaluation" / "answer-quality-v1.json",
        CORPUS_DIR,
        SEARCH_SUITE,
    )

    expected_sources = {
        "q1",
        "paraphrase-p1",
        "q2",
        "paraphrase-p2",
        "q5",
        "q6",
        "negative-n1",
        "negative-n3",
    }

    assert len(suite.cases) == 8
    assert {case.source_case_id for case in suite.cases} == expected_sources

    by_source = {case.source_case_id: case for case in suite.cases}

    assert by_source["q1"].allowed_answer_statuses == [
        "partial",
        "insufficient_evidence",
    ]
    assert (
        by_source["q1"].evidence_passage_ids
        == by_source["paraphrase-p1"].evidence_passage_ids
    )

    for source_id in ("negative-n1", "negative-n3"):
        case = by_source[source_id]
        assert case.allowed_answer_statuses == ["insufficient_evidence"]
        assert case.evidence_passage_ids
        assert case.required_limitations
        assert case.required_points == []

    for source_id in expected_sources - {
        "q1",
        "negative-n1",
        "negative-n3",
    }:
        case = by_source[source_id]
        assert case.allowed_answer_statuses == ["answered"]
        assert case.required_points
