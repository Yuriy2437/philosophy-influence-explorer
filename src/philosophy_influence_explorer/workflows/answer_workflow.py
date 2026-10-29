"""Compose retrieval and structured generation without configuring providers."""

from __future__ import annotations

from typing import NotRequired

from langgraph.graph import END, START, StateGraph

from philosophy_influence_explorer.generation.base import AnswerGenerator
from philosophy_influence_explorer.generation.contracts import (
    GroundedAnswer,
    validate_answer_references,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphRetriever,
)
from philosophy_influence_explorer.workflows.retrieval_workflow import (
    RetrievalState,
    build_retrieval_workflow,
)


class AnswerState(RetrievalState):
    """Keep unvalidated generator output separate from the accepted answer."""

    draft_answer: NotRequired[GroundedAnswer]
    answer: NotRequired[GroundedAnswer]


def build_answer_workflow(
    retriever: SemanticGraphRetriever,
    generator: AnswerGenerator,
):
    """Compile retrieval, generation, and structural validation."""
    retrieval_graph = build_retrieval_workflow(retriever)

    def generate_answer(state: AnswerState) -> dict:
        draft = generator.generate(
            query_text=state["query_text"],
            evidence=state["evidence"],
        )
        return {"draft_answer": draft}

    def validate_answer_structure(state: AnswerState) -> dict:
        draft = state["draft_answer"]
        if not isinstance(draft, GroundedAnswer):
            raise ValueError("Generator must return GroundedAnswer.")

        answer = GroundedAnswer.model_validate(draft.model_dump())
        validate_answer_references(answer, state["evidence"])
        return {"answer": answer}

    builder = StateGraph(AnswerState)
    builder.add_node("retrieve_evidence", retrieval_graph)
    builder.add_node("generate_answer", generate_answer)
    builder.add_node("validate_answer_structure", validate_answer_structure)
    builder.add_edge(START, "retrieve_evidence")
    builder.add_edge("retrieve_evidence", "generate_answer")
    builder.add_edge("generate_answer", "validate_answer_structure")
    builder.add_edge("validate_answer_structure", END)
    return builder.compile()
