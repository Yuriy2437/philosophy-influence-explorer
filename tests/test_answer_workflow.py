"""Test answer orchestration without an LLM, database, or embedding service."""

from __future__ import annotations

from unittest.mock import create_autospec, patch

import pytest

from philosophy_influence_explorer.generation.base import AnswerGenerator
from philosophy_influence_explorer.generation.contracts import (
    AnswerClaim,
    GroundedAnswer,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    RetrievedPassage,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphResult,
    SemanticGraphRetriever,
)
from philosophy_influence_explorer.workflows.answer_workflow import (
    build_answer_workflow,
)


def synthetic_passage() -> RetrievedPassage:
    return RetrievedPassage(
        id="passage:test",
        text="Synthetic editorial evidence, not a quotation.",
        score=0.8,
        source_id="source:test",
        work_id="work:test",
        citation_label="Synthetic fixture",
        language="en",
        text_kind="editorial_summary",
        review_status="curated",
        is_verbatim=False,
        is_editorial=True,
        is_machine_generated=False,
        concepts=(),
    )


def dependencies():
    retriever = create_autospec(SemanticGraphRetriever, instance=True)
    generator = create_autospec(AnswerGenerator, instance=True)
    retriever.retrieve.return_value = SemanticGraphResult(
        (synthetic_passage(),),
        (),
    )
    return retriever, generator


def supported_answer(passage_id: str = "passage:test") -> GroundedAnswer:
    return GroundedAnswer(
        status="partial",
        claims=[
            AnswerClaim(
                text="Synthetic assertion.",
                passage_ids=[passage_id],
            )
        ],
        limitations=["Synthetic evidence is limited."],
    )


def test_graph_passes_prepared_evidence_and_validates_answer() -> None:
    retriever, generator = dependencies()
    expected = supported_answer()
    generator.generate.return_value = expected

    state = build_answer_workflow(retriever, generator).invoke(
        {"query_text": "  synthetic question  "}
    )

    assert state["answer"] == expected
    assert state["draft_answer"] == expected
    assert state["query_text"] == "synthetic question"
    assert state["retrieval_result"].semantic_passages[0].score == 0.8
    assert state["evidence"].passages[0].is_editorial is True
    generator.generate.assert_called_once_with(
        query_text="synthetic question",
        evidence=state["evidence"],
    )


def test_unknown_reference_is_rejected_by_graph() -> None:
    retriever, generator = dependencies()
    generator.generate.return_value = supported_answer("passage:unknown")

    with pytest.raises(ValueError, match="outside supplied evidence"):
        build_answer_workflow(retriever, generator).invoke(
            {"query_text": "question"})


def test_empty_evidence_can_produce_insufficient_answer() -> None:
    retriever, generator = dependencies()
    retriever.retrieve.return_value = SemanticGraphResult((), ())
    generator.generate.return_value = GroundedAnswer(
        status="insufficient_evidence",
        claims=[],
        limitations=["No evidence was supplied."],
    )

    state = build_answer_workflow(retriever, generator).invoke({
        "query_text": "question"})

    assert state["answer"].status == "insufficient_evidence"
    assert state["answer"].claims == []
    assert state["evidence"].passages == ()


def test_generation_failure_propagates() -> None:
    retriever, generator = dependencies()
    generator.generate.side_effect = RuntimeError(
        "Synthetic generation failure")

    with pytest.raises(RuntimeError, match="Synthetic generation failure"):
        build_answer_workflow(retriever, generator).invoke(
            {"query_text": "question"})


def test_retrieval_failure_prevents_generation() -> None:
    retriever, generator = dependencies()
    retriever.retrieve.side_effect = RuntimeError(
        "Synthetic retrieval failure")

    with pytest.raises(RuntimeError, match="Synthetic retrieval failure"):
        build_answer_workflow(retriever, generator).invoke(
            {"query_text": "question"})

    generator.generate.assert_not_called()


def test_invalid_request_prevents_generation() -> None:
    retriever, generator = dependencies()

    with pytest.raises(ValueError, match="query_text must not be blank"):
        build_answer_workflow(retriever, generator).invoke(
            {"query_text": "   "})

    retriever.retrieve.assert_not_called()
    generator.generate.assert_not_called()


def test_wrong_generator_return_type_is_rejected() -> None:
    retriever, generator = dependencies()
    generator.generate.return_value = {"status": "answered"}

    with pytest.raises(ValueError, match="must return GroundedAnswer"):
        build_answer_workflow(retriever, generator).invoke(
            {"query_text": "question"})


def test_mutated_answer_is_revalidated() -> None:
    retriever, generator = dependencies()
    answer = supported_answer()
    answer.claims.clear()
    generator.generate.return_value = answer

    with pytest.raises(ValueError, match="require claims"):
        build_answer_workflow(retriever, generator).invoke(
            {"query_text": "question"})


def test_unknown_reference_in_later_claim_is_rejected() -> None:
    retriever, generator = dependencies()
    generator.generate.return_value = GroundedAnswer(
        status="answered",
        claims=[
            AnswerClaim(
                text="First synthetic assertion.",
                passage_ids=["passage:test"],
            ),
            AnswerClaim(
                text="Second synthetic assertion.",
                passage_ids=["passage:unknown"],
            ),
        ],
        limitations=[],
    )

    with pytest.raises(ValueError, match="outside supplied evidence"):
        build_answer_workflow(retriever, generator).invoke(
            {"query_text": "question"})


def test_claims_cannot_reference_passages_when_evidence_is_empty() -> None:
    retriever, generator = dependencies()
    retriever.retrieve.return_value = SemanticGraphResult((), ())
    generator.generate.return_value = supported_answer()

    with pytest.raises(ValueError, match="outside supplied evidence"):
        build_answer_workflow(retriever, generator).invoke(
            {"query_text": "question"})


def test_evidence_preparation_failure_prevents_generation() -> None:
    retriever, generator = dependencies()
    workflow = build_answer_workflow(retriever, generator)

    with patch(
        "philosophy_influence_explorer.workflows.retrieval_workflow.prepare_evidence",
        side_effect=ValueError("Synthetic evidence conflict"),
    ):
        with pytest.raises(ValueError, match="Synthetic evidence conflict"):
            workflow.invoke({"query_text": "question"})

    generator.generate.assert_not_called()


def test_second_invocation_does_not_return_previous_answer() -> None:
    retriever, generator = dependencies()
    generator.generate.side_effect = [
        supported_answer(),
        RuntimeError("Second generation failed"),
    ]
    workflow = build_answer_workflow(retriever, generator)

    first_state = workflow.invoke({"query_text": "first question"})
    assert first_state["answer"].status == "partial"

    with pytest.raises(RuntimeError, match="Second generation failed"):
        workflow.invoke({"query_text": "second question"})

    assert generator.generate.call_count == 2


def test_nonempty_evidence_can_produce_insufficient_answer() -> None:
    retriever, generator = dependencies()
    expected = GroundedAnswer(
        status="insufficient_evidence",
        claims=[],
        limitations=[
            "The supplied passage does not explain the requested distinction."
        ],
    )
    generator.generate.return_value = expected

    state = build_answer_workflow(retriever, generator).invoke(
        {"query_text": "Explain the requested distinction."}
    )

    assert len(state["evidence"].passages) == 1
    assert state["answer"] == expected
    assert state["answer"].claims == []

    generator.generate.assert_called_once_with(
        query_text="Explain the requested distinction.",
        evidence=state["evidence"],
    )


def test_additional_graph_passage_can_support_answer() -> None:
    from dataclasses import replace

    from philosophy_influence_explorer.retrieval.graph_context_retriever import (
        GraphContextEdge,
        GraphContextPassage,
        GraphContextPath,
    )
    from philosophy_influence_explorer.retrieval.passage_retriever import (
        PassageConcept,
    )

    retriever, generator = dependencies()

    concept = PassageConcept(
        id="concept:synthetic",
        canonical_label="Synthetic concept",
        concept_family="synthetic",
        label_en="Synthetic concept",
        label_ru="Синтетическое понятие",
        label_de="Synthetischer Begriff",
    )
    seed = replace(synthetic_passage(), concepts=(concept,))

    related = GraphContextPassage(
        id="passage:graph-related",
        text="Additional synthetic editorial evidence.",
        source_id="source:graph-related",
        work_id="work:graph-related",
        citation_label="Synthetic graph fixture",
        language="en",
        text_kind="editorial_summary",
        review_status="curated",
        is_verbatim=False,
        is_editorial=True,
        is_machine_generated=False,
    )

    path = GraphContextPath(
        seed_id=seed.id,
        concept=concept,
        seed_edge=GraphContextEdge(
            id="edge:synthetic-seed",
            from_id=seed.id,
            to_id=concept.id,
            review_status="curated",
            extraction_method="manual",
            confidence=None,
        ),
        related_edge=GraphContextEdge(
            id="edge:synthetic-related",
            from_id=related.id,
            to_id=concept.id,
            review_status="curated",
            extraction_method="manual",
            confidence=None,
        ),
        passage=related,
    )

    retriever.retrieve.return_value = SemanticGraphResult(
        (seed,),
        (path,),
    )
    expected = GroundedAnswer(
        status="partial",
        claims=[
            AnswerClaim(
                text="Additional synthetic editorial evidence is supplied.",
                passage_ids=[related.id],
            )
        ],
        limitations=["The supplied material is synthetic editorial evidence."],
    )
    generator.generate.return_value = expected

    state = build_answer_workflow(retriever, generator).invoke(
        {"query_text": "What additional evidence is supplied?"}
    )

    evidence = state["evidence"]

    assert len(state["retrieval_result"].graph_context) == 1
    assert {passage.id for passage in evidence.passages} == {
        seed.id,
        related.id,
    }
    assert len(evidence.passages) == 2
    assert evidence.semantic_passage_ids == (seed.id,)
    assert evidence.additional_graph_passage_ids == (related.id,)
    assert next(
        passage for passage in evidence.passages
        if passage.id == related.id
    ) == related

    generator.generate.assert_called_once_with(
        query_text="What additional evidence is supplied?",
        evidence=evidence,
    )
    assert state["answer"] == expected
    assert state["answer"].claims[0].passage_ids == [related.id]
