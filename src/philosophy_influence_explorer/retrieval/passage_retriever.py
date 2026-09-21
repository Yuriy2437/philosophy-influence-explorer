"""Semantic retrieval of curated Passage nodes from Neo4j."""

from __future__ import annotations

from dataclasses import dataclass

from neo4j.exceptions import Neo4jError

from philosophy_influence_explorer.embeddings.base import EmbeddingProvider
from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient
from philosophy_influence_explorer.retrieval.passage_indexer import (
    DATASET_ID,
    PASSAGE_EMBEDDING_INDEX,
)


@dataclass(frozen=True)
class RetrievedPassage:
    """One semantically retrieved curated passage."""

    id: str
    text: str
    score: float
    source_id: str
    work_id: str
    citation_label: str
    language: str
    text_kind: str
    is_verbatim: bool
    is_editorial: bool
    is_machine_generated: bool


class PassageRetriever:
    """Retrieve curated passages using the configured embedding provider."""

    def __init__(
        self,
        *,
        client: Neo4jClient,
        provider: EmbeddingProvider,
    ) -> None:
        self._client = client
        self._provider = provider

    def search(
        self,
        query_text: str,
        *,
        limit: int = 5,
    ) -> list[RetrievedPassage]:
        """Embed a query and return its most similar curated passages."""
        normalized_query = query_text.strip()

        if not normalized_query:
            raise ValueError("query_text must not be blank.")

        if limit < 1:
            raise ValueError("limit must be at least 1.")

        query_embedding = self._provider.embed_query(normalized_query)

        expected_dimensions = self._provider.model_info.dimensions
        if len(query_embedding) != expected_dimensions:
            raise RuntimeError(
                "Embedding provider returned a query vector with an "
                f"unexpected dimension: expected {expected_dimensions}, "
                f"got {len(query_embedding)}."
            )

        cypher = """
        CALL db.index.vector.queryNodes(
            $index_name,
            $candidate_limit,
            $query_embedding
        )
        YIELD node, score
        WHERE node:Passage
          AND node.dataset = $dataset_id
          AND node.embedding_provider = $provider
          AND node.embedding_model = $model
          AND node.embedding_dimensions = $dimensions
        RETURN node.id AS id,
               node.text AS text,
               score AS score,
               node.source_id AS source_id,
               node.work_id AS work_id,
               node.citation_label AS citation_label,
               node.language AS language,
               node.text_kind AS text_kind,
               node.is_verbatim AS is_verbatim,
               node.is_editorial AS is_editorial,
               node.is_machine_generated AS is_machine_generated
        ORDER BY score DESC, id ASC
        LIMIT $limit
        """

        candidate_limit = max(limit * 4, limit)

        try:
            with self._client.session() as session:
                result = session.run(
                    cypher,
                    index_name=PASSAGE_EMBEDDING_INDEX,
                    candidate_limit=candidate_limit,
                    query_embedding=query_embedding,
                    dataset_id=DATASET_ID,
                    provider=self._provider.model_info.provider,
                    model=self._provider.model_info.model,
                    dimensions=expected_dimensions,
                    limit=limit,
                )
                records = list(result)
        except Neo4jError as error:
            raise RuntimeError(
                "Unable to search curated Passage embeddings in Neo4j."
            ) from error

        return [
            RetrievedPassage(
                id=record["id"],
                text=record["text"],
                score=float(record["score"]),
                source_id=record["source_id"],
                work_id=record["work_id"],
                citation_label=record["citation_label"],
                language=record["language"],
                text_kind=record["text_kind"],
                is_verbatim=record["is_verbatim"],
                is_editorial=record["is_editorial"],
                is_machine_generated=record["is_machine_generated"],
            )
            for record in records
        ]
