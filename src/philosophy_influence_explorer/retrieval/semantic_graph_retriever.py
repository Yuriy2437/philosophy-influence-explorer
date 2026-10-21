"""Compose semantic passage retrieval and explicit graph context."""

from __future__ import annotations

from dataclasses import dataclass

from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextPath,
    GraphContextRetriever,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageRetriever,
    PassageSearchFilters,
    RetrievedPassage,
)


@dataclass(frozen=True)
class SemanticGraphResult:
    """Keep semantic matches separate from graph-derived context paths."""

    semantic_passages: tuple[RetrievedPassage, ...]
    graph_context: tuple[GraphContextPath, ...]


class SemanticGraphRetriever:
    """Retrieve semantic seeds and expand them using the same filters."""

    def __init__(
        self,
        *,
        passage_retriever: PassageRetriever,
        graph_context_retriever: GraphContextRetriever,
    ) -> None:
        self._passage_retriever = passage_retriever
        self._graph_context_retriever = graph_context_retriever

    def retrieve(
        self,
        query_text: str,
        *,
        limit: int = 5,
        graph_limit: int = 20,
        filters: PassageSearchFilters | None = None,
    ) -> SemanticGraphResult:
        """Run semantic retrieval once, then return bounded graph paths.

        The graph limit is global across all semantic seeds.
        Graph paths are not reranked or merged into semantic matches.
        Dependency failures propagate instead of becoming empty results.
        """
        normalized_query = query_text.strip()

        if not normalized_query:
            raise ValueError("query_text must not be blank.")

        if limit < 1:
            raise ValueError("limit must be at least 1.")

        if graph_limit < 1:
            raise ValueError("graph_limit must be at least 1.")

        normalized_filters = (
            filters.normalized()
            if filters is not None
            else PassageSearchFilters()
        )

        passages = self._passage_retriever.search(
            normalized_query,
            limit=limit,
            filters=normalized_filters,
        )

        if not passages:
            return SemanticGraphResult(
                semantic_passages=(),
                graph_context=(),
            )

        seed_ids = list(dict.fromkeys(passage.id for passage in passages))

        paths = self._graph_context_retriever.expand(
            seed_ids,
            limit=graph_limit,
            filters=normalized_filters,
        )

        return SemanticGraphResult(
            semantic_passages=tuple(passages),
            graph_context=tuple(paths),
        )
