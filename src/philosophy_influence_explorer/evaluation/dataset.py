"""Load and validate historical semantic-search evaluation data."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr

LABELS = {
    "directly_relevant",
    "partially_relevant",
    "thematically_related",
    "irrelevant",
}


class EvaluationModel(BaseModel):
    """Reject unknown fields and implicit value conversions."""

    model_config = ConfigDict(extra="forbid", strict=True)


class SearchFilters(EvaluationModel):
    concept_family: StrictStr | None
    language: StrictStr | None
    is_verbatim: StrictBool | None
    is_editorial: StrictBool | None


class HistoricalContext(EvaluationModel):
    evaluation_date: StrictStr
    dataset_id: StrictStr
    reported_corpus_passages: StrictInt = Field(gt=0)
    embedding_provider: StrictStr
    embedding_model: StrictStr
    embedding_dimensions: StrictInt = Field(gt=0)


class SearchCase(EvaluationModel):
    id: StrictStr = Field(min_length=1)
    source_section: StrictStr = Field(min_length=1)
    query: StrictStr = Field(min_length=1)
    limit: StrictInt = Field(gt=0)
    filters: SearchFilters
    expected_passage_id: StrictStr | None
    historical_expected_rank: StrictInt | None
    historical_top_result_relevance: StrictStr
    historical_direct_answer_in_top3: StrictBool


class SearchSuite(EvaluationModel):
    schema_version: StrictInt
    suite_id: StrictStr = Field(min_length=1)
    description: StrictStr
    source_document: StrictStr
    historical_context: HistoricalContext
    cases: list[SearchCase] = Field(min_length=1)


class Judgment(EvaluationModel):
    passage_id: StrictStr = Field(min_length=1)
    historical_rank: StrictInt = Field(gt=0)
    relevance: StrictStr
    rationale: StrictStr = Field(min_length=1)


class CaseJudgments(EvaluationModel):
    case_id: StrictStr = Field(min_length=1)
    judgments: list[Judgment] = Field(min_length=1)


class JudgmentSet(EvaluationModel):
    schema_version: StrictInt
    suite_id: StrictStr
    source_document: StrictStr
    approval_date: StrictStr
    annotation_method: StrictStr
    scope: StrictStr
    relevance_labels: list[StrictStr]
    cases: list[CaseJudgments] = Field(min_length=1)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_evaluation(
    suite_path: Path,
    judgments_path: Path,
) -> tuple[SearchSuite, JudgmentSet]:
    """Load matching files and validate their historical consistency."""
    suite = SearchSuite.model_validate(json.loads(suite_path.read_text(encoding="utf-8-sig")))
    judgments = JudgmentSet.model_validate(
        json.loads(judgments_path.read_text(encoding="utf-8-sig"))
    )

    _require(
        suite.schema_version == judgments.schema_version == 1,
        "Unsupported schema version.",
    )
    _require(suite.suite_id == judgments.suite_id, "Suite IDs do not match.")
    _require(
        suite.source_document == judgments.source_document,
        "Source documents do not match.",
    )
    _require(
        len(judgments.relevance_labels) == len(LABELS)
        and set(judgments.relevance_labels) == LABELS,
        "Invalid relevance labels.",
    )

    case_ids = [case.id for case in suite.cases]
    judgment_ids = [case.case_id for case in judgments.cases]
    _require(len(case_ids) == len(set(case_ids)), "Duplicate search case ID.")
    _require(
        len(judgment_ids) == len(set(judgment_ids)),
        "Duplicate judgment case ID.",
    )
    _require(set(case_ids) == set(judgment_ids), "Case IDs do not match.")

    judgments_by_id = {case.case_id: case for case in judgments.cases}

    for case in suite.cases:
        prefix = f"{case.id}: "
        _require(bool(case.id.strip()), prefix + "Blank case ID.")
        _require(bool(case.query.strip()), prefix + "Blank query.")
        _require(
            case.limit == 3,
            prefix + "Schema v1 historical cases require limit=3.",
        )
        _require(
            case.historical_top_result_relevance in LABELS,
            prefix + "Invalid top-result relevance.",
        )

        items = judgments_by_id[case.id].judgments
        passage_ids = [item.passage_id for item in items]
        ranks = [item.historical_rank for item in items]
        _require(
            len(passage_ids) == len(set(passage_ids)),
            prefix + "Duplicate passage judgment.",
        )
        _require(
            sorted(ranks) == list(range(1, case.limit + 1)),
            prefix + "Historical ranks must cover 1 through limit.",
        )

        for item in items:
            _require(bool(item.passage_id.strip()), prefix + "Blank passage ID.")
            _require(bool(item.rationale.strip()), prefix + "Blank rationale.")
            _require(item.relevance in LABELS, prefix + "Invalid relevance.")

        top = next(item for item in items if item.historical_rank == 1)
        _require(
            top.relevance == case.historical_top_result_relevance,
            prefix + "Top-result relevance mismatch.",
        )
        has_direct = any(item.relevance == "directly_relevant" for item in items)
        _require(
            has_direct == case.historical_direct_answer_in_top3,
            prefix + "Direct-answer summary mismatch.",
        )

        if case.expected_passage_id is None:
            _require(
                case.historical_expected_rank is None,
                prefix + "Rank without expected passage.",
            )
        else:
            _require(
                bool(case.expected_passage_id.strip()),
                prefix + "Blank expected passage ID.",
            )
            expected = next(
                (item for item in items if item.passage_id == case.expected_passage_id),
                None,
            )
            _require(expected is not None, prefix + "Expected passage not judged.")
            _require(
                expected is not None and expected.historical_rank == case.historical_expected_rank,
                prefix + "Expected passage rank mismatch.",
            )

    return suite, judgments
