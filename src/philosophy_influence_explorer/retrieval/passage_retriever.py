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
class PassageConcept:
    """A curated Concept directly discussed by a retrieved Passage."""

    id: str
    canonical_label: str
    concept_family: str
    label_en: str
    label_ru: str
    label_de: str


@dataclass(frozen=True)
class PassageSearchFilters:
    """Optional graph and provenance filters for semantic passage retrieval."""

    concept_family: str | None = None
    language: str | None = None
    is_verbatim: bool | None = None
    is_editorial: bool | None = None

    def normalized(self) -> PassageSearchFilters:
        """Return a copy with blank string filters normalized to None."""
        return PassageSearchFilters(
            concept_family=_normalize_optional_text(self.concept_family),
            language=_normalize_optional_text(self.language),
            is_verbatim=self.is_verbatim,
            is_editorial=self.is_editorial,
        )


@dataclass(frozen=True)
class RetrievedPassage:
    """One semantically retrieved curated passage and its graph provenance."""

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
    concepts: tuple[PassageConcept, ...]


class PassageRetriever:
    """Retrieve curated passages using embeddings and graph-aware filters."""

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
        filters: PassageSearchFilters | None = None,
    ) -> list[RetrievedPassage]:
        """Embed a query and return matching curated passages by similarity."""
        normalized_query = query_text.strip()

        if not normalized_query:
            raise ValueError("query_text must not be blank.")

        if limit < 1:
            raise ValueError("limit must be at least 1.")

        normalized_filters = (
            filters.normalized()
            if filters is not None
            else PassageSearchFilters()
        )

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
          AND (
              $language IS NULL
              OR node.language = $language
          )
          AND (
              $is_verbatim IS NULL
              OR node.is_verbatim = $is_verbatim
          )
          AND (
              $is_editorial IS NULL
              OR node.is_editorial = $is_editorial
          )
        OPTIONAL MATCH (node)-[:DISCUSSES]->(concept:Concept {
            dataset: $dataset_id
        })
        WITH node, score, collect(
            CASE
                WHEN concept IS NULL THEN NULL
                ELSE {
                    id: concept.id,
                    canonical_label: concept.canonical_label,
                    concept_family: concept.concept_family,
                    label_en: concept.label_en,
                    label_ru: concept.label_ru,
                    label_de: concept.label_de
                }
            END
        ) AS collected_concepts
        WITH node,
             score,
             [concept IN collected_concepts WHERE concept IS NOT NULL]
                 AS concepts
        WHERE $concept_family IS NULL
           OR ANY(
               concept IN concepts
               WHERE concept.concept_family = $concept_family
           )
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
               node.is_machine_generated AS is_machine_generated,
               concepts AS concepts
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
                    language=normalized_filters.language,
                    is_verbatim=normalized_filters.is_verbatim,
                    is_editorial=normalized_filters.is_editorial,
                    concept_family=normalized_filters.concept_family,
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
                concepts=tuple(
                    PassageConcept(
                        id=concept["id"],
                        canonical_label=concept["canonical_label"],
                        concept_family=concept["concept_family"],
                        label_en=concept["label_en"],
                        label_ru=concept["label_ru"],
                        label_de=concept["label_de"],
                    )
                    for concept in record["concepts"]
                ),
            )
            for record in records
        ]


def _normalize_optional_text(value: str | None) -> str | None:
    """Strip optional text and treat blanks as absent filters."""
    if value is None:
        return None

    normalized_value = value.strip()
    return normalized_value or None
