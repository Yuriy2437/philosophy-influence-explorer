"""Load fixed-evidence answer evaluation cases without external services."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from philosophy_influence_explorer.ingestion.validators import (
    validate_curated_corpus,
)

AnswerStatus = Literal["answered", "partial", "insufficient_evidence"]


class AnswerEvaluationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class AnswerCase(AnswerEvaluationModel):
    id: str = Field(min_length=1)
    source_case_id: str = Field(min_length=1)
    query: str = Field(min_length=1, max_length=500)
    evidence_passage_ids: list[str] = Field(min_length=1)
    allowed_answer_statuses: list[AnswerStatus] = Field(min_length=1)
    required_points: list[str]
    required_limitations: list[str]
    forbidden_inferences: list[str]
    rationale: str = Field(min_length=1)

    @field_validator("id", "source_case_id", "query", "rationale")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text must not be blank.")
        if value != value.strip():
            raise ValueError("Text must not have surrounding whitespace.")
        return value

    @field_validator(
        "evidence_passage_ids",
        "required_points",
        "required_limitations",
        "forbidden_inferences",
    )
    @classmethod
    def validate_text_lists(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or value != value.strip() for value in values):
            raise ValueError("List entries must be nonblank and trimmed.")
        if len(values) != len(set(values)):
            raise ValueError("Duplicate list entry.")
        return values

    @field_validator("allowed_answer_statuses")
    @classmethod
    def reject_duplicate_statuses(
        cls,
        values: list[AnswerStatus],
    ) -> list[AnswerStatus]:
        if len(values) != len(set(values)):
            raise ValueError("Duplicate answer status.")
        return values


class AnswerSuite(AnswerEvaluationModel):
    schema_version: Literal[1]
    suite_id: Literal["answer-quality-v1"]
    mode: Literal["fixed_evidence"]
    description: str = Field(min_length=1)
    cases: list[AnswerCase] = Field(min_length=1)

    @field_validator("description")
    @classmethod
    def reject_blank_description(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("Description must be nonblank and trimmed.")
        return value


def load_answer_evaluation(
    suite_path: Path,
    corpus_dir: Path,
    search_suite_path: Path,
) -> AnswerSuite:
    """Validate cases against current corpus and source question identities."""
    suite = AnswerSuite.model_validate(
        json.loads(suite_path.read_text(encoding="utf-8-sig"))
    )

    case_ids = [case.id for case in suite.cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Duplicate answer case ID.")

    source_ids = [case.source_case_id for case in suite.cases]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate source case ID.")

    search_data = json.loads(search_suite_path.read_text(encoding="utf-8-sig"))
    source_cases: dict[str, str] = {}

    for item in search_data["cases"]:
        source_id = item["id"]
        if source_id in source_cases:
            raise ValueError("Duplicate source search case ID.")
        source_cases[source_id] = item["query"]

    corpus = validate_curated_corpus(corpus_dir)
    passage_ids = {passage.id for passage in corpus["passages"]}

    for case in suite.cases:
        if case.source_case_id not in source_cases:
            raise ValueError(f"{case.id}: Unknown source case ID.")

        if case.query != source_cases[case.source_case_id]:
            raise ValueError(f"{case.id}: Source query mismatch.")

        unknown = set(case.evidence_passage_ids) - passage_ids
        if unknown:
            raise ValueError(
                f"{case.id}: Unknown evidence passage IDs: "
                + ", ".join(sorted(unknown))
            )

    return suite
