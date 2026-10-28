"""Test the compiled retrieval graph with an isolated dependency."""

from __future__ import annotations

from unittest.mock import create_autospec

import pytest

from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageSearchFilters,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphResult,
    SemanticGraphRetriever,
)
from philosophy_influence_explorer.workflows.retrieval_workflow import (
    build_retrieval_workflow,
)


def test_graph_normalizes_request_and_preserves_result() -> None:
    retriever = create_autospec(SemanticGraphRetriever, instance=True)
    expected = SemanticGraphResult(semantic_passages=(), graph_context=())
    retriever.retrieve.return_value = expected
    graph = build_retrieval_workflow(retriever)

    result = graph.invoke(
        {
            "query_text": "  being and becoming  ",
            "limit": 3,
            "graph_limit": 7,
            "filters": PassageSearchFilters(
                language=" ru ",
                concept_family=" dialectic ",
                is_verbatim=True,
                is_editorial=False,
            ),
        }
    )

    filters = PassageSearchFilters(
        language="ru",
        concept_family="dialectic",
        is_verbatim=True,
        is_editorial=False,
    )
    retriever.retrieve.assert_called_once_with(
        "being and becoming",
        limit=3,
        graph_limit=7,
        filters=filters,
    )
    assert result["query_text"] == "being and becoming"
    assert result["retrieval_result"] == expected
    assert result["evidence"].passages == ()
    assert result["evidence"].semantic_passage_ids == ()
    assert result["evidence"].additional_graph_passage_ids == ()


def test_graph_applies_defaults() -> None:
    retriever = create_autospec(SemanticGraphRetriever, instance=True)
    retriever.retrieve.return_value = SemanticGraphResult((), ())
    graph = build_retrieval_workflow(retriever)

    graph.invoke({"query_text": "becoming"})

    retriever.retrieve.assert_called_once_with(
        "becoming",
        limit=5,
        graph_limit=20,
        filters=PassageSearchFilters(),
    )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"query_text": "   "}, "query_text must not be blank"),
        ({"query_text": 123}, "query_text must be a string"),
        ({"limit": 0}, "limit must be a positive integer"),
        ({"limit": True}, "limit must be a positive integer"),
        ({"limit": 1.5}, "limit must be a positive integer"),
        ({"graph_limit": -1}, "graph_limit must be a positive integer"),
        ({"filters": {}}, "filters must be PassageSearchFilters"),
    ],
)
def test_graph_rejects_invalid_input_before_retrieval(
    overrides: dict,
    message: str,
) -> None:
    retriever = create_autospec(SemanticGraphRetriever, instance=True)
    graph = build_retrieval_workflow(retriever)

    with pytest.raises(ValueError, match=message):
        graph.invoke({"query_text": "becoming", **overrides})

    retriever.retrieve.assert_not_called()


def test_graph_propagates_retrieval_failure() -> None:
    retriever = create_autospec(SemanticGraphRetriever, instance=True)
    retriever.retrieve.side_effect = RuntimeError("Synthetic retrieval failure")
    graph = build_retrieval_workflow(retriever)

    with pytest.raises(RuntimeError, match="Synthetic retrieval failure"):
        graph.invoke({"query_text": "becoming"})


def test_graph_invocations_do_not_reuse_previous_result() -> None:
    retriever = create_autospec(SemanticGraphRetriever, instance=True)
    first = SemanticGraphResult((), ())
    retriever.retrieve.side_effect = [
        first,
        RuntimeError("Second invocation failed"),
    ]
    graph = build_retrieval_workflow(retriever)

    result = graph.invoke({"query_text": "first question"})
    assert result["retrieval_result"] == first

    with pytest.raises(RuntimeError, match="Second invocation failed"):
        graph.invoke({"query_text": "second question"})

    assert retriever.retrieve.call_count == 2
