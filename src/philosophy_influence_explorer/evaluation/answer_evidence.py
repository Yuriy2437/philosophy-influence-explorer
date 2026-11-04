"""Build fixed evaluation evidence without retrieval or external services."""

from __future__ import annotations

from collections.abc import Sequence

from philosophy_influence_explorer.evaluation.answer_dataset import AnswerCase
from philosophy_influence_explorer.ingestion.models import PassageRecord
from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextPassage,
)
from philosophy_influence_explorer.workflows.evidence import EvidencePacket


def build_fixed_evidence(
    case: AnswerCase,
    passages: Sequence[PassageRecord],
) -> EvidencePacket:
    """Select exact corpus records in case order without retrieval membership."""
    selected_ids = case.evidence_passage_ids

    if not selected_ids:
        raise ValueError("Fixed evidence must contain passage IDs.")

    if any(
        not passage_id.strip() or passage_id != passage_id.strip()
        for passage_id in selected_ids
    ):
        raise ValueError("Evidence passage IDs must be nonblank and trimmed.")

    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("Duplicate evidence passage ID.")

    records: dict[str, PassageRecord] = {}

    for passage in passages:
        if passage.id in records:
            raise ValueError(f"Duplicate corpus passage ID: {passage.id}")
        records[passage.id] = passage

    unknown = set(selected_ids) - records.keys()
    if unknown:
        raise ValueError(
            "Unknown evidence passage IDs: " + ", ".join(sorted(unknown))
        )

    evidence_passages = []

    for passage_id in selected_ids:
        record = records[passage_id]
        evidence_passages.append(
            GraphContextPassage(
                id=record.id,
                text=record.text,
                source_id=record.source_id,
                work_id=record.work_id,
                citation_label=record.citation_label,
                language=record.language,
                text_kind=record.text_kind.value,
                review_status=record.review_status.value,
                is_verbatim=record.is_verbatim,
                is_editorial=record.is_editorial,
                is_machine_generated=record.is_machine_generated,
            )
        )

    return EvidencePacket(
        passages=tuple(evidence_passages),
        semantic_passage_ids=(),
        additional_graph_passage_ids=(),
    )
