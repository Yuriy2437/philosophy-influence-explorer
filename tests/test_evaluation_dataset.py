"""Validate evaluation fixtures without database or embedding services."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from philosophy_influence_explorer.evaluation.dataset import load_evaluation

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "data/evaluation/semantic-search-v1.json"
JUDGMENTS_PATH = ROOT / "data/evaluation/semantic-search-judgments-v1.json"


def test_repository_evaluation_data() -> None:
    suite, judgments = load_evaluation(SUITE_PATH, JUDGMENTS_PATH)

    assert len(suite.cases) == 12
    assert sum(case.expected_passage_id is not None for case in suite.cases) == 9
    assert sum(len(case.judgments) for case in judgments.cases) == 36

    counts = Counter(item.relevance for case in judgments.cases for item in case.judgments)
    assert counts == {
        "directly_relevant": 8,
        "partially_relevant": 1,
        "thematically_related": 19,
        "irrelevant": 8,
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("suite_id", "Suite IDs"),
        ("duplicate_case", "Duplicate search case"),
        ("missing_case", "Case IDs"),
        ("duplicate_passage", "Duplicate passage"),
        ("rank", "Historical ranks"),
        ("label", "Invalid relevance"),
        ("top_summary", "Top-result relevance"),
        ("direct_summary", "Direct-answer summary"),
        ("expected_rank", "Expected passage rank"),
        ("blank_query", "Blank query"),
    ],
)
def test_inconsistent_data_is_rejected(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8-sig"))
    judgments = json.loads(JUDGMENTS_PATH.read_text(encoding="utf-8-sig"))
    first_case = suite["cases"][0]
    first_judgments = judgments["cases"][0]["judgments"]

    if mutation == "suite_id":
        judgments["suite_id"] = "another-suite"
    elif mutation == "duplicate_case":
        suite["cases"].append(first_case)
    elif mutation == "missing_case":
        judgments["cases"].pop()
    elif mutation == "duplicate_passage":
        first_judgments[1]["passage_id"] = first_judgments[0]["passage_id"]
    elif mutation == "rank":
        first_judgments[1]["historical_rank"] = 1
    elif mutation == "label":
        first_judgments[1]["relevance"] = "unknown"
    elif mutation == "top_summary":
        first_case["historical_top_result_relevance"] = "irrelevant"
    elif mutation == "direct_summary":
        first_case["historical_direct_answer_in_top3"] = True
    elif mutation == "expected_rank":
        first_case["historical_expected_rank"] = 2
    elif mutation == "blank_query":
        first_case["query"] = "   "

    suite_path = tmp_path / "suite.json"
    judgments_path = tmp_path / "judgments.json"
    suite_path.write_text(json.dumps(suite, ensure_ascii=False), encoding="utf-8")
    judgments_path.write_text(
        json.dumps(judgments, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        load_evaluation(suite_path, judgments_path)
