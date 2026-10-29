"""HTTP contracts for operator-only answer generation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from philosophy_influence_explorer.generation.contracts import GroundedAnswer


class AnswerRequest(BaseModel):
    """Bounded request; model and system instructions are server-controlled."""

    model_config = ConfigDict(extra="forbid", strict=True)

    q: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=3, ge=1, le=5)
    graph_limit: int = Field(default=20, ge=1, le=20)
    concept_family: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default=None, max_length=20)
    is_verbatim: bool = True
    is_editorial: bool = False

    @field_validator("q")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Question must not be blank.")
        return normalized

    @field_validator("concept_family", "language")
    @classmethod
    def normalize_optional_filter(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class AnswerEvidencePassage(BaseModel):
    """Passage provenance without an invented similarity score."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    text: str
    source_id: str
    work_id: str
    citation_label: str
    language: str
    text_kind: str
    review_status: str
    is_verbatim: bool
    is_editorial: bool
    is_machine_generated: bool


class AnswerEvidenceResponse(BaseModel):
    """The full passage packet supplied to the generator."""

    model_config = ConfigDict(extra="forbid", strict=True)

    passages: list[AnswerEvidencePassage]
    semantic_passage_ids: list[str]
    additional_graph_passage_ids: list[str]


class AnswerResponse(BaseModel):
    """A validated answer and its supplied evidence, not scholarly approval."""

    model_config = ConfigDict(extra="forbid", strict=True)

    query: str
    mode: Literal["evidence_grounded_answer"] = "evidence_grounded_answer"
    answer: GroundedAnswer
    evidence: AnswerEvidenceResponse
