"""Prepare unique passage records without assessing answer sufficiency."""

from __future__ import annotations

from dataclasses import dataclass, fields

from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextPassage,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphResult,
)


@dataclass(frozen=True)
class EvidencePacket:
    """Unique passage records and their retrieval membership.

    Semantic scores and all graph paths remain in SemanticGraphResult.
    Membership does not establish relevance or independent corroboration.
    """

    passages: tuple[GraphContextPassage, ...]
    semantic_passage_ids: tuple[str, ...]
    additional_graph_passage_ids: tuple[str, ...]


def prepare_evidence(result: SemanticGraphResult) -> EvidencePacket:
    """Deduplicate passage records while rejecting conflicting provenance."""
    records: dict[str, GraphContextPassage] = {}
    semantic_ids: list[str] = []
    additional_ids: list[str] = []
    passage_fields = fields(GraphContextPassage)

    def register(passage: GraphContextPassage) -> bool:
        if not passage.id.strip():
            raise ValueError("Evidence passage ID must not be blank.")

        existing = records.get(passage.id)
        if existing is not None:
            if existing != passage:
                raise ValueError(f"Conflicting evidence records for passage {passage.id!r}.")
            return False

        records[passage.id] = passage
        return True

    for passage in result.semantic_passages:
        record = GraphContextPassage(
            **{field.name: getattr(passage, field.name) for field in passage_fields}
        )
        if register(record):
            semantic_ids.append(record.id)

    semantic_id_set = set(semantic_ids)

    for path in result.graph_context:
        if path.seed_id not in semantic_id_set:
            raise ValueError("Graph path seed is absent from semantic results.")

        if register(path.passage):
            additional_ids.append(path.passage.id)

    return EvidencePacket(
        passages=tuple(records.values()),
        semantic_passage_ids=tuple(semantic_ids),
        additional_graph_passage_ids=tuple(additional_ids),
    )
