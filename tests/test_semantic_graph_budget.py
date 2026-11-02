"""Test cooperative budgets around composed retrieval stages."""

from __future__ import annotations

from unittest.mock import Mock, create_autospec

import pytest

from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextRetriever,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageRetriever,
    PassageSearchFilters,
    RetrievedPassage,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphResult,
    SemanticGraphRetriever,
)
from philosophy_influence_explorer.time_budget import (
    ExecutionBudget,
    ExecutionBudgetExceededError,
)


def dependencies():
    passage_retriever = create_autospec(PassageRetriever, instance=True)
    graph_retriever = create_autospec(GraphContextRetriever, instance=True)

    passage = Mock(spec=RetrievedPassage)
    passage.id = "passage:test"

    passage_retriever.search.return_value = [passage]
    graph_retriever.expand.return_value = []

    retriever = SemanticGraphRetriever(
        passage_retriever=passage_retriever,
        graph_context_retriever=graph_retriever,
    )

    return retriever, passage_retriever, graph_retriever, passage


def test_expired_budget_prevents_all_retrieval_calls() -> None:
    now = [100.0]
    budget = ExecutionBudget(5.0, clock=lambda: now[0])
    retriever, passages, graph, _ = dependencies()
    now[0] = 105.0

    with pytest.raises(ExecutionBudgetExceededError):
        retriever.retrieve("question", budget=budget)

    passages.search.assert_not_called()
    graph.expand.assert_not_called()


@pytest.mark.parametrize("empty_result", [False, True])
def test_expiry_after_search_prevents_graph_expansion(
    empty_result: bool,
) -> None:
    now = [100.0]
    budget = ExecutionBudget(5.0, clock=lambda: now[0])
    retriever, passages, graph, passage = dependencies()

    def slow_search(*args, **kwargs):
        assert kwargs["budget"] is budget
        now[0] = 105.0
        return [] if empty_result else [passage]

    passages.search.side_effect = slow_search

    with pytest.raises(ExecutionBudgetExceededError):
        retriever.retrieve("question", budget=budget)

    passages.search.assert_called_once()
    graph.expand.assert_not_called()


def test_expiry_after_graph_expansion_rejects_result() -> None:
    now = [100.0]
    budget = ExecutionBudget(5.0, clock=lambda: now[0])
    retriever, passages, graph, _ = dependencies()

    def slow_expand(*args, **kwargs):
        now[0] = 105.0
        return []

    graph.expand.side_effect = slow_expand

    with pytest.raises(ExecutionBudgetExceededError):
        retriever.retrieve("question", budget=budget)

    passages.search.assert_called_once()
    graph.expand.assert_called_once()


def test_sufficient_budget_preserves_result_and_arguments() -> None:
    now = [100.0]
    budget = ExecutionBudget(5.0, clock=lambda: now[0])
    retriever, passages, graph, passage = dependencies()
    filters = PassageSearchFilters(language=" en ")

    result = retriever.retrieve(
        "  question  ",
        limit=2,
        graph_limit=7,
        filters=filters,
        budget=budget,
    )

    assert result == SemanticGraphResult(
        semantic_passages=(passage,),
        graph_context=(),
    )
    passages.search.assert_called_once_with(
        "question",
        limit=2,
        filters=PassageSearchFilters(language="en"),
        budget=budget,
    )
    graph.expand.assert_called_once_with(
        ["passage:test"],
        limit=7,
        filters=PassageSearchFilters(language="en"),
    )
