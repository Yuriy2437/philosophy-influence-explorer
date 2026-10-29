"""Structured answer contracts and evidence-reference checks."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from philosophy_influence_explorer.workflows.evidence import EvidencePacket


class AnswerClaim(BaseModel):
    """One generated assertion with passage-level references."""

    model_config = ConfigDict(extra="forbid", strict=True)

    text: str = Field(min_length=1)
    passage_ids: list[str] = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Claim text must not be blank.")
        return normalized

    @field_validator("passage_ids")
    @classmethod
    def normalize_passage_ids(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Passage IDs must not be blank.")
        if len(normalized) != len(set(normalized)):
            raise ValueError("Duplicate passage references in a claim.")
        return normalized


class GroundedAnswer(BaseModel):
    """Generator output; structural validity is not scholarly approval."""

    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["answered", "partial", "insufficient_evidence"]
    claims: list[AnswerClaim]
    limitations: list[str]

    @field_validator("limitations")
    @classmethod
    def normalize_limitations(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Limitations must not contain blank entries.")
        return normalized

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        if self.status == "insufficient_evidence":
            if self.claims:
                raise ValueError("insufficient_evidence must not contain claims.")
            if not self.limitations:
                raise ValueError("insufficient_evidence requires an explanation.")
        else:
            if not self.claims:
                raise ValueError("answered and partial require claims.")
            if self.status == "partial" and not self.limitations:
                raise ValueError("partial requires limitations.")
        return self


def validate_answer_references(
    answer: GroundedAnswer,
    evidence: EvidencePacket,
) -> None:
    """Reject references outside the supplied evidence packet.

    This checks reference membership only. It does not establish
    entailment, quotation accuracy, or answer completeness.
    """
    available_ids = {passage.id for passage in evidence.passages}
    referenced_ids = {passage_id for claim in answer.claims for passage_id in claim.passage_ids}
    unknown_ids = referenced_ids - available_ids

    if unknown_ids:
        raise ValueError(
            "Answer references passages outside supplied evidence: "
            + ", ".join(sorted(unknown_ids))
        )
