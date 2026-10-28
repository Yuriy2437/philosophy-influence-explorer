"""Test evidence preparation using synthetic passage and graph records."""

from __future__ import annotations

from dataclasses import asdict, replace
from unittest.mock import create_autospec

import pytest

from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextEdge,
    GraphContextPassage,
    GraphContextPath,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageConcept,
    RetrievedPassage,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphResult,
    SemanticGraphRetriever,
)
from philosophy_influence_explorer.workflows.evidence import prepare_evidence
from philosophy_influence_explorer.workflows.retrieval_workflow import (
    build_retrieval_workflow,
)


def passage(passage_id: str) -> GraphContextPassage:
    return GraphContextPassage(
        id=passage_id,
        text="Synthetic editorial summary, not a quotation.",
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


def semantic(record: GraphContextPassage) -> RetrievedPassage:
    return RetrievedPassage(
        **asdict(record),
        score=0.8,
        concepts=(),
    )


def path(
    seed_id: str,
    record: GraphContextPassage,
    concept_id: str = "concept:test",
) -> GraphContextPath:
    return GraphContextPath(
        seed_id=seed_id,
        concept=PassageConcept(
            id=concept_id,
            canonical_label="Test",
            concept_family="test",
            label_en="Test",
            label_ru="Тест",
            label_de="Test",
        ),
        seed_edge=GraphContextEdge(
            id=f"edge:{seed_id}:{concept_id}",
            from_id=seed_id,
            to_id=concept_id,
            review_status="curated",
            extraction_method="manual",
            confidence=None,
        ),
        related_edge=GraphContextEdge(
            id=f"edge:{record.id}:{concept_id}",
            from_id=record.id,
            to_id=concept_id,
            review_status="curated",
            extraction_method="manual",
            confidence=None,
        ),
        passage=record,
    )


def test_empty_result_produces_empty_packet() -> None:
    packet = prepare_evidence(SemanticGraphResult((), ()))

    assert packet.passages == ()
    assert packet.semantic_passage_ids == ()
    assert packet.additional_graph_passage_ids == ()


def test_unique_passages_preserve_semantic_then_graph_order() -> None:
    first = passage("passage:first")
    second = passage("passage:second")
    additional = passage("passage:additional")
    paths = (
        path(first.id, second),
        path(first.id, additional),
        path(first.id, additional, "concept:other"),
    )
    result = SemanticGraphResult(
        (semantic(first), semantic(second)),
        paths,
    )

    packet = prepare_evidence(result)

    assert packet.passages == (first, second, additional)
    assert packet.semantic_passage_ids == (first.id, second.id)
    assert packet.additional_graph_passage_ids == (additional.id,)
    assert result.graph_context == paths
    assert len(result.graph_context) == 3
    assert result.semantic_passages[0].score == 0.8
    assert not hasattr(packet.passages[-1], "score")


def test_duplicate_semantic_record_is_not_repeated() -> None:
    record = passage("passage:first")
    retrieved = semantic(record)

    packet = prepare_evidence(SemanticGraphResult((retrieved, retrieved), ()))

    assert packet.passages == (record,)
    assert packet.semantic_passage_ids == (record.id,)


@pytest.mark.parametrize(
    "changes",
    [
        {"text": "Different text"},
        {"source_id": "source:different"},
        {"is_verbatim": True},
        {"review_status": "reviewed"},
    ],
)
def test_conflicting_record_is_rejected(changes: dict) -> None:
    record = passage("passage:first")
    conflicting = replace(record, **changes)
    result = SemanticGraphResult(
        (semantic(record),),
        (path(record.id, conflicting),),
    )

    with pytest.raises(ValueError, match="Conflicting evidence records"):
        prepare_evidence(result)


def test_unknown_graph_seed_is_rejected() -> None:
    result = SemanticGraphResult(
        (semantic(passage("passage:first")),),
        (path("passage:missing", passage("passage:additional")),),
    )

    with pytest.raises(ValueError, match="seed is absent"):
        prepare_evidence(result)


def test_compiled_graph_prepares_nonempty_evidence() -> None:
    first = passage("passage:first")
    second = passage("passage:second")
    additional = passage("passage:additional")
    paths = (
        path(first.id, second),
        path(first.id, additional),
        path(first.id, additional, "concept:other"),
    )
    retrieved = SemanticGraphResult(
        (semantic(first), semantic(second)),
        paths,
    )
    retriever = create_autospec(SemanticGraphRetriever, instance=True)
    retriever.retrieve.return_value = retrieved
    graph = build_retrieval_workflow(retriever)

    state = graph.invoke(
        {
            "query_text": "  synthetic question  ",
            "limit": 2,
            "graph_limit": 10,
        }
    )

    assert state["query_text"] == "synthetic question"
    assert state["retrieval_result"] == retrieved
    assert state["retrieval_result"].graph_context == paths

    evidence = state["evidence"]
    assert evidence.passages == (first, second, additional)
    assert evidence.semantic_passage_ids == (first.id, second.id)
    assert evidence.additional_graph_passage_ids == (additional.id,)
    assert evidence.passages[-1].is_editorial is True
    assert evidence.passages[-1].text_kind == "editorial_summary"
    assert not hasattr(evidence.passages[-1], "score")
    retriever.retrieve.assert_called_once()


def test_compiled_graph_propagates_evidence_conflict() -> None:
    record = passage("passage:first")
    conflicting = replace(record, text="Conflicting synthetic text.")
    retriever = create_autospec(SemanticGraphRetriever, instance=True)
    retriever.retrieve.return_value = SemanticGraphResult(
        (semantic(record),),
        (path(record.id, conflicting),),
    )
    graph = build_retrieval_workflow(retriever)

    with pytest.raises(ValueError, match="Conflicting evidence records"):
        graph.invoke({"query_text": "synthetic question"})

    retriever.retrieve.assert_called_once()
