"""Retrieve bounded passage context through shared curated concepts."""

from __future__ import annotations

from dataclasses import dataclass

from neo4j.exceptions import Neo4jError

from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient
from philosophy_influence_explorer.retrieval.passage_indexer import DATASET_ID
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageConcept,
    PassageSearchFilters,
)

_ALLOWED_EDGE_STATUSES = ("reviewed", "curated")


@dataclass(frozen=True)
class GraphContextEdge:
    """One directed DISCUSSES edge with its recorded annotation metadata."""

    id: str
    from_id: str
    to_id: str
    review_status: str
    extraction_method: str | None
    confidence: float | None
    relation_type: str = "DISCUSSES"


@dataclass(frozen=True)
class GraphContextPassage:
    """Related passage with provenance, without an invented vector score."""

    id: str
    text: str
    source_id: str
    work_id: str
    citation_label: str
    language: str
    text_kind: str
    review_status: str
    is_verbatim: bool
    is_editorial: bool
    is_machine_generated: bool


@dataclass(frozen=True)
class GraphContextPath:
    """A seed -> concept <- related passage path."""

    seed_id: str
    concept: PassageConcept
    seed_edge: GraphContextEdge
    related_edge: GraphContextEdge
    passage: GraphContextPassage


class GraphContextRetriever:
    """Expand seed passages through two explicitly accepted DISCUSSES edges."""

    def __init__(self, *, client: Neo4jClient) -> None:
        self._client = client

    def expand(
        self,
        seed_ids: list[str],
        *,
        limit: int = 20,
        filters: PassageSearchFilters | None = None,
    ) -> list[GraphContextPath]:
        """Return at most limit paths, globally across all supplied seeds.

        Filters constrain related passages and the shared concept.
        They do not re-filter seed passages supplied by the caller.
        Edge acceptance and passage review status are separate concerns:
        only reviewed/curated edges are traversed, while passage status
        is returned unchanged. This is context retrieval, not approval
        of the retrieved text or a claim of historical influence.
        """
        if limit < 1:
            raise ValueError("limit must be at least 1.")

        normalized_seed_ids = sorted({seed_id.strip() for seed_id in seed_ids})

        if any(not seed_id for seed_id in normalized_seed_ids):
            raise ValueError("seed_ids must not contain blank IDs.")

        if not normalized_seed_ids:
            return []

        normalized_filters = (
            filters.normalized()
            if filters is not None
            else PassageSearchFilters()
        )

        query = """
        MATCH (seed:Passage)-[seed_edge:DISCUSSES]->
              (concept:Concept)<-[related_edge:DISCUSSES]-
              (related:Passage)
        WHERE seed.id IN $seed_ids
          AND seed.dataset = $dataset_id
          AND concept.dataset = $dataset_id
          AND related.dataset = $dataset_id
          AND seed_edge.dataset = $dataset_id
          AND related_edge.dataset = $dataset_id
          AND seed_edge.id IS NOT NULL
          AND related_edge.id IS NOT NULL
          AND seed_edge.review_status IN $allowed_edge_statuses
          AND related_edge.review_status IN $allowed_edge_statuses
          AND related.id <> seed.id
          AND (
              $language IS NULL
              OR related.language = $language
          )
          AND (
              $is_verbatim IS NULL
              OR related.is_verbatim = $is_verbatim
          )
          AND (
              $is_editorial IS NULL
              OR related.is_editorial = $is_editorial
          )
          AND (
              $concept_family IS NULL
              OR concept.concept_family = $concept_family
          )
        WITH DISTINCT seed, concept, seed_edge, related_edge, related
        ORDER BY seed.id ASC,
                 concept.id ASC,
                 related.id ASC,
                 seed_edge.id ASC,
                 related_edge.id ASC
        LIMIT $limit
        RETURN seed.id AS seed_id,
               concept {
                   .id,
                   .canonical_label,
                   .concept_family,
                   .label_en,
                   .label_ru,
                   .label_de
               } AS concept,
               seed_edge {
                   .id,
                   .review_status,
                   .extraction_method,
                   .confidence,
                   from_id: seed.id,
                   to_id: concept.id
               } AS seed_edge,
               related_edge {
                   .id,
                   .review_status,
                   .extraction_method,
                   .confidence,
                   from_id: related.id,
                   to_id: concept.id
               } AS related_edge,
               related {
                   .id,
                   .text,
                   .source_id,
                   .work_id,
                   .citation_label,
                   .language,
                   .text_kind,
                   .review_status,
                   .is_verbatim,
                   .is_editorial,
                   .is_machine_generated
               } AS passage
        """

        try:
            with self._client.session() as session:
                records = list(
                    session.run(
                        query,
                        seed_ids=normalized_seed_ids,
                        dataset_id=DATASET_ID,
                        allowed_edge_statuses=list(_ALLOWED_EDGE_STATUSES),
                        language=normalized_filters.language,
                        is_verbatim=normalized_filters.is_verbatim,
                        is_editorial=normalized_filters.is_editorial,
                        concept_family=normalized_filters.concept_family,
                        limit=limit,
                    )
                )
        except Neo4jError as error:
            raise RuntimeError(
                "Unable to retrieve graph context from Neo4j."
            ) from error

        return [
            GraphContextPath(
                seed_id=record["seed_id"],
                concept=PassageConcept(**record["concept"]),
                seed_edge=GraphContextEdge(**record["seed_edge"]),
                related_edge=GraphContextEdge(**record["related_edge"]),
                passage=GraphContextPassage(**record["passage"]),
            )
            for record in records
        ]
