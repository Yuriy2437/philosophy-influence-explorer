"""Test answer structure and reference membership without an LLM."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from philosophy_influence_explorer.generation.contracts import (
    AnswerClaim,
    GroundedAnswer,
    validate_answer_references,
)
from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextPassage,
)
from philosophy_influence_explorer.workflows.evidence import EvidencePacket


def evidence_packet() -> EvidencePacket:
    passage = GraphContextPassage(
        id="passage:test",
        text="Synthetic evidence, not a quotation.",
        source_id="source:test",
        work_id="work:test",
        citation_label="Synthetic fixture",
        language="en",
        text_kind="editorial_summary",
        review_status="curated",
        is_verbatim=False,
        is_editorial=True,
        is_machine_generated=False,
    )
    return EvidencePacket(
        passages=(passage,),
        semantic_passage_ids=(passage.id,),
        additional_graph_passage_ids=(),
    )


def test_valid_answer_normalizes_text_and_references() -> None:
    answer = GroundedAnswer(
        status="answered",
        claims=[
            AnswerClaim(
                text="  Synthetic assertion.  ",
                passage_ids=[" passage:test "],
            )
        ],
        limitations=[],
    )

    validate_answer_references(answer, evidence_packet())

    assert answer.claims[0].text == "Synthetic assertion."
    assert answer.claims[0].passage_ids == ["passage:test"]


@pytest.mark.parametrize(
    "claim",
    [
        {"text": "   ", "passage_ids": ["passage:test"]},
        {"text": "Assertion", "passage_ids": []},
        {"text": "Assertion", "passage_ids": ["   "]},
        {
            "text": "Assertion",
            "passage_ids": ["passage:test", " passage:test "],
        },
    ],
)
def test_invalid_claim_is_rejected(claim: dict) -> None:
    with pytest.raises(ValidationError):
        AnswerClaim.model_validate(claim)


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "answered", "claims": [], "limitations": []},
        {"status": "partial", "claims": [], "limitations": ["Missing context"]},
        {
            "status": "partial",
            "claims": [{"text": "Assertion", "passage_ids": ["passage:test"]}],
            "limitations": [],
        },
        {"status": "insufficient_evidence", "claims": [], "limitations": []},
        {
            "status": "insufficient_evidence",
            "claims": [{"text": "Assertion", "passage_ids": ["passage:test"]}],
            "limitations": ["Missing context"],
        },
        {
            "status": "insufficient_evidence",
            "claims": [],
            "limitations": ["   "],
        },
    ],
)
def test_inconsistent_answer_status_is_rejected(payload: dict) -> None:
    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate(payload)


def test_partial_answer_with_limitations_is_valid() -> None:
    answer = GroundedAnswer(
        status="partial",
        claims=[AnswerClaim(text="Assertion", passage_ids=["passage:test"])],
        limitations=["  The evidence does not explain why.  "],
    )

    validate_answer_references(answer, evidence_packet())

    assert answer.limitations == ["The evidence does not explain why."]


def test_insufficient_evidence_can_be_reported_without_passages() -> None:
    answer = GroundedAnswer(
        status="insufficient_evidence",
        claims=[],
        limitations=["No suitable evidence was supplied."],
    )

    validate_answer_references(answer, EvidencePacket((), (), ()))


def test_unknown_passage_reference_is_rejected() -> None:
    answer = GroundedAnswer(
        status="answered",
        claims=[AnswerClaim(text="Assertion", passage_ids=[
                            "passage:unknown"])],
        limitations=[],
    )

    with pytest.raises(ValueError, match="outside supplied evidence"):
        validate_answer_references(answer, evidence_packet())


def test_extra_answer_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate(
            {
                "status": "insufficient_evidence",
                "claims": [],
                "limitations": ["No evidence"],
                "unverified_conclusion": "An unsupported conclusion",
            }
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"text": 123, "passage_ids": ["passage:test"]},
        {"text": "Assertion", "passage_ids": "passage:test"},
        {"text": "Assertion", "passage_ids": [123]},
    ],
)
def test_claim_rejects_wrong_field_types(payload: dict) -> None:
    with pytest.raises(ValidationError):
        AnswerClaim.model_validate(payload)


def test_extra_claim_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AnswerClaim.model_validate(
            {
                "text": "Assertion",
                "passage_ids": ["passage:test"],
                "unverified_source": "Unexpected value",
            }
        )


@pytest.mark.parametrize(
    "payload",
    [
        {
            "status": "insufficient_evidence",
            "claims": {},
            "limitations": ["No suitable evidence"],
        },
        {
            "status": "insufficient_evidence",
            "claims": [],
            "limitations": [123],
        },
    ],
)
def test_answer_rejects_wrong_field_types(payload: dict) -> None:
    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate(payload)
