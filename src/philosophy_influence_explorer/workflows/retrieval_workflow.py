"""Explicit LangGraph orchestration of existing retrieval services."""

from __future__ import annotations

from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageSearchFilters,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphResult,
    SemanticGraphRetriever,
)
from philosophy_influence_explorer.workflows.evidence import (
    EvidencePacket,
    prepare_evidence,
)


class RetrievalState(TypedDict):
    """Request parameters and retrieval output for one graph invocation."""

    query_text: str
    limit: NotRequired[int]
    graph_limit: NotRequired[int]
    filters: NotRequired[PassageSearchFilters]
    retrieval_result: NotRequired[SemanticGraphResult]
    evidence: NotRequired[EvidencePacket]


def validate_request(state: RetrievalState) -> dict:
    """Normalize input before any retrieval dependency is called."""
    query_text = state["query_text"]

    if not isinstance(query_text, str):
        raise ValueError("query_text must be a string.")

    normalized_query = query_text.strip()
    if not normalized_query:
        raise ValueError("query_text must not be blank.")

    limit = state.get("limit", 5)
    graph_limit = state.get("graph_limit", 20)

    for name, value in (("limit", limit), ("graph_limit", graph_limit)):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer.")

    filters = state.get("filters", PassageSearchFilters())
    if not isinstance(filters, PassageSearchFilters):
        raise ValueError("filters must be PassageSearchFilters.")

    return {
        "query_text": normalized_query,
        "limit": limit,
        "graph_limit": graph_limit,
        "filters": filters.normalized(),
    }


def build_retrieval_workflow(retriever: SemanticGraphRetriever):
    """Compile a fresh graph without configuring external services."""

    def retrieve_context(state: RetrievalState) -> dict:
        result = retriever.retrieve(
            state["query_text"],
            limit=state["limit"],
            graph_limit=state["graph_limit"],
            filters=state["filters"],
        )
        return {"retrieval_result": result}

    def prepare_evidence_node(state: RetrievalState) -> dict:
        return {
            "evidence": prepare_evidence(state["retrieval_result"]),
        }

    builder = StateGraph(RetrievalState)
    builder.add_node("validate_request", validate_request)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("prepare_evidence", prepare_evidence_node)
    builder.add_edge(START, "validate_request")
    builder.add_edge("validate_request", "retrieve_context")
    builder.add_edge("retrieve_context", "prepare_evidence")
    builder.add_edge("prepare_evidence", END)
    return builder.compile()
