"""Unit tests for semantic retrieval and graph expansion composition."""

from __future__ import annotations

from unittest.mock import Mock, create_autospec

import pytest

from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextPath,
    GraphContextRetriever,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageRetriever,
    PassageSearchFilters,
    RetrievedPassage,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphRetriever,
)


def _dependencies():
    semantic = create_autospec(PassageRetriever, instance=True)
    graph = create_autospec(GraphContextRetriever, instance=True)
    return semantic, graph


def test_retrieve_preserves_results_and_passes_normalized_filters() -> None:
    semantic, graph = _dependencies()
    first = Mock(spec=RetrievedPassage, id="passage:first")
    second = Mock(spec=RetrievedPassage, id="passage:second")
    path = Mock(spec=GraphContextPath)

    semantic.search.return_value = [first, second]
    graph.expand.return_value = [path]

    retriever = SemanticGraphRetriever(
        passage_retriever=semantic,
        graph_context_retriever=graph,
    )

    result = retriever.retrieve(
        "  being and becoming  ",
        limit=3,
        graph_limit=7,
        filters=PassageSearchFilters(
            language=" ru ",
            concept_family=" dialectic ",
            is_verbatim=True,
            is_editorial=False,
        ),
    )

    expected_filters = PassageSearchFilters(
        language="ru",
        concept_family="dialectic",
        is_verbatim=True,
        is_editorial=False,
    )

    semantic.search.assert_called_once_with(
        "being and becoming",
        limit=3,
        filters=expected_filters,
    )
    graph.expand.assert_called_once_with(
        ["passage:first", "passage:second"],
        limit=7,
        filters=expected_filters,
    )

    assert result.semantic_passages == (first, second)
    assert result.graph_context == (path,)


def test_retrieve_empty_semantic_results_skips_graph() -> None:
    semantic, graph = _dependencies()
    semantic.search.return_value = []

    result = SemanticGraphRetriever(
        passage_retriever=semantic,
        graph_context_retriever=graph,
    ).retrieve("nothing")

    assert result.semantic_passages == ()
    assert result.graph_context == ()
    graph.expand.assert_not_called()


def test_retrieve_defaults_and_deduplicates_only_seed_ids() -> None:
    semantic, graph = _dependencies()
    passage = Mock(spec=RetrievedPassage, id="passage:seed")
    first_path = Mock(spec=GraphContextPath)
    second_path = Mock(spec=GraphContextPath)

    semantic.search.return_value = [passage, passage]
    graph.expand.return_value = [first_path, second_path]

    result = SemanticGraphRetriever(
        passage_retriever=semantic,
        graph_context_retriever=graph,
    ).retrieve("becoming")

    semantic.search.assert_called_once_with(
        "becoming",
        limit=5,
        filters=PassageSearchFilters(),
    )
    graph.expand.assert_called_once_with(
        ["passage:seed"],
        limit=20,
        filters=PassageSearchFilters(),
    )

    assert result.semantic_passages == (passage, passage)
    assert result.graph_context == (first_path, second_path)


@pytest.mark.parametrize(
    ("query_text", "limit", "graph_limit", "message"),
    [
        ("   ", 5, 20, "query_text must not be blank"),
        ("becoming", 0, 20, "limit must be at least 1"),
        ("becoming", 5, 0, "graph_limit must be at least 1"),
    ],
)
def test_retrieve_rejects_invalid_input_before_dependencies(
    query_text: str,
    limit: int,
    graph_limit: int,
    message: str,
) -> None:
    semantic, graph = _dependencies()
    retriever = SemanticGraphRetriever(
        passage_retriever=semantic,
        graph_context_retriever=graph,
    )

    with pytest.raises(ValueError, match=message):
        retriever.retrieve(
            query_text,
            limit=limit,
            graph_limit=graph_limit,
        )

    semantic.search.assert_not_called()
    graph.expand.assert_not_called()


def test_retrieve_semantic_failure_does_not_call_graph() -> None:
    semantic, graph = _dependencies()
    semantic.search.side_effect = RuntimeError("Semantic search failed")

    retriever = SemanticGraphRetriever(
        passage_retriever=semantic,
        graph_context_retriever=graph,
    )

    with pytest.raises(RuntimeError, match="Semantic search failed"):
        retriever.retrieve("becoming")

    graph.expand.assert_not_called()


def test_retrieve_graph_failure_is_not_silently_ignored() -> None:
    semantic, graph = _dependencies()
    semantic.search.return_value = [
        Mock(spec=RetrievedPassage, id="passage:seed")
    ]
    graph.expand.side_effect = RuntimeError("Graph expansion failed")

    retriever = SemanticGraphRetriever(
        passage_retriever=semantic,
        graph_context_retriever=graph,
    )

    with pytest.raises(RuntimeError, match="Graph expansion failed"):
        retriever.retrieve("becoming")
