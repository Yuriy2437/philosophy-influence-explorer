"""Build evaluation reports without calling external services."""

from __future__ import annotations

from dataclasses import asdict

from philosophy_influence_explorer.evaluation.dataset import (
    CaseJudgments,
    SearchCase,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    RetrievedPassage,
)


def build_case_report(
    case: SearchCase,
    judgments: CaseJudgments,
    passages: list[RetrievedPassage] | None,
    *,
    error_type: str | None = None,
) -> dict:
    """Compare current results with historical pair-level judgments.

    Historical labels are reference annotations, not a fresh assessment
    of current passage texts. An error is not a successful empty result.
    """
    if case.id != judgments.case_id:
        raise ValueError("Case and judgment IDs do not match.")

    if error_type is not None:
        if not error_type.strip():
            raise ValueError("error_type must not be blank.")
        if passages is not None:
            raise ValueError("Failed queries must not contain results.")
    elif passages is None:
        raise ValueError("Successful queries require a result list.")

    report = {
        "case_id": case.id,
        "query": case.query,
        "limit": case.limit,
        "filters": case.filters.model_dump(),
        "status": "error" if error_type is not None else "success",
        "error_type": error_type,
        "expected_passage_id": case.expected_passage_id,
        "historical_expected_rank": case.historical_expected_rank,
        "current_expected_rank": None,
        "expected_passage_found": None,
        "returned_count": None,
        "all_results_match_filters": None,
        "unjudged_count": None,
        "results": [],
        "annotation_scope": (
            "Historical query-passage judgments only. Current passage "
            "texts have not been verified against historical snapshots."
        ),
    }

    if error_type is not None:
        return report

    assert passages is not None

    if len(passages) > case.limit:
        raise ValueError("Result count exceeds the requested limit.")

    ids = [passage.id for passage in passages]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate passage IDs in search results.")

    known = {item.passage_id: item for item in judgments.judgments}
    filters = case.filters
    results = []

    for rank, passage in enumerate(passages, start=1):
        violations = []

        for field in ("language", "is_verbatim", "is_editorial"):
            expected = getattr(filters, field)
            if expected is not None and getattr(passage, field) != expected:
                violations.append(field)

        if filters.concept_family is not None and not any(
            concept.concept_family == filters.concept_family for concept in passage.concepts
        ):
            violations.append("concept_family")

        historical = known.get(passage.id)
        results.append(
            {
                "rank": rank,
                "passage": asdict(passage),
                "filter_violations": violations,
                "historical_judgment": (
                    {
                        "relevance": historical.relevance,
                        "rationale": historical.rationale,
                        "historical_rank": historical.historical_rank,
                        "current_text_verified": False,
                    }
                    if historical is not None
                    else None
                ),
            }
        )

    expected_rank = (
        ids.index(case.expected_passage_id) + 1 if case.expected_passage_id in ids else None
    )

    report.update(
        current_expected_rank=expected_rank,
        expected_passage_found=(
            expected_rank is not None if case.expected_passage_id is not None else None
        ),
        returned_count=len(results),
        all_results_match_filters=all(not result["filter_violations"] for result in results),
        unjudged_count=sum(result["historical_judgment"] is None for result in results),
        results=results,
    )
    return report
