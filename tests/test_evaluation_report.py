"""Test report semantics without live retrieval."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from philosophy_influence_explorer.evaluation.dataset import load_evaluation
from philosophy_influence_explorer.evaluation.report import build_case_report
from philosophy_influence_explorer.retrieval.passage_retriever import (
    RetrievedPassage,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def evaluation():
    return load_evaluation(
        ROOT / "data/evaluation/semantic-search-v1.json",
        ROOT / "data/evaluation/semantic-search-judgments-v1.json",
    )


def make_passage(
    passage_id: str,
    *,
    language: str = "en",
    is_editorial: bool = False,
) -> RetrievedPassage:
    return RetrievedPassage(
        id=passage_id,
        text="Synthetic test passage, not a corpus quotation.",
        score=0.8,
        source_id="source:test",
        work_id="work:test",
        citation_label="Synthetic fixture",
        language=language,
        text_kind="primary_quote",
        review_status="candidate",
        is_verbatim=True,
        is_editorial=is_editorial,
        is_machine_generated=False,
        concepts=(),
    )


def test_judgments_follow_passage_ids_not_current_rank(evaluation):
    suite, judgments = evaluation
    case = suite.cases[0]
    passage_id = case.expected_passage_id
    assert passage_id is not None

    report = build_case_report(
        case,
        judgments.cases[0],
        [make_passage("passage:unknown"), make_passage(passage_id)],
    )

    assert report["current_expected_rank"] == 2
    assert report["expected_passage_found"] is True
    assert report["unjudged_count"] == 1
    assert report["results"][0]["historical_judgment"] is None
    historical = report["results"][1]["historical_judgment"]
    assert historical["relevance"] == "partially_relevant"
    assert historical["historical_rank"] == 1
    assert historical["current_text_verified"] is False
    json.dumps(report, ensure_ascii=False)


def test_successful_empty_result_is_not_an_error(evaluation):
    suite, judgments = evaluation
    report = build_case_report(suite.cases[0], judgments.cases[0], [])

    assert report["status"] == "success"
    assert report["returned_count"] == 0
    assert report["expected_passage_found"] is False
    assert report["all_results_match_filters"] is True


def test_error_has_no_success_metrics(evaluation):
    suite, judgments = evaluation
    report = build_case_report(
        suite.cases[0],
        judgments.cases[0],
        None,
        error_type="RuntimeError",
    )

    assert report["status"] == "error"
    assert report["returned_count"] is None
    assert report["expected_passage_found"] is None
    assert report["all_results_match_filters"] is None


def test_negative_case_has_no_target_success_claim(evaluation):
    suite, judgments = evaluation
    case = next(case for case in suite.cases if case.id == "negative-n1")
    labels = next(item for item in judgments.cases if item.case_id == case.id)
    report = build_case_report(case, labels, [make_passage("passage:unknown")])

    assert report["expected_passage_found"] is None
    assert report["unjudged_count"] == 1


def test_provenance_violation_is_reported(evaluation):
    suite, judgments = evaluation
    report = build_case_report(
        suite.cases[0],
        judgments.cases[0],
        [make_passage("passage:test", is_editorial=True)],
    )

    assert report["all_results_match_filters"] is False
    assert report["results"][0]["filter_violations"] == ["is_editorial"]


def test_duplicate_results_are_rejected(evaluation):
    suite, judgments = evaluation
    passage = make_passage("passage:test")

    with pytest.raises(ValueError, match="Duplicate passage"):
        build_case_report(suite.cases[0], judgments.cases[0], [passage, passage])


def test_error_cannot_include_results(evaluation):
    suite, judgments = evaluation

    with pytest.raises(ValueError, match="must not contain results"):
        build_case_report(
            suite.cases[0],
            judgments.cases[0],
            [],
            error_type="RuntimeError",
        )
