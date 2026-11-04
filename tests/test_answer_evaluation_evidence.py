"""Test fixed evidence construction without database or model calls."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from philosophy_influence_explorer.evaluation.answer_dataset import (
    AnswerCase,
    load_answer_evaluation,
)
from philosophy_influence_explorer.evaluation.answer_evidence import (
    build_fixed_evidence,
)
from philosophy_influence_explorer.ingestion.models import PassageRecord
from philosophy_influence_explorer.ingestion.validators import (
    load_csv_records,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "data" / "curated"
EVALUATION_DIR = ROOT / "data" / "evaluation"


@pytest.fixture
def corpus_passages() -> list[PassageRecord]:
    return load_csv_records(
        CORPUS_DIR / "passages.csv",
        PassageRecord,
    )


def make_case(passage_ids: list[str]) -> AnswerCase:
    return AnswerCase(
        id="synthetic-evidence-case",
        source_case_id="q5",
        query="Synthetic test question?",
        evidence_passage_ids=passage_ids,
        allowed_answer_statuses=["answered"],
        required_points=["Synthetic review criterion."],
        required_limitations=[],
        forbidden_inferences=[],
        rationale="Synthetic fixture, not an approved evaluation case.",
    )


def test_preserves_selection_order_and_has_no_retrieval_membership(
    corpus_passages: list[PassageRecord],
) -> None:
    ids = [
        "passage:hegel:wl:being:de",
        "passage:kant:groundwork:2:humanity:en",
    ]
    case = make_case(ids)
    original_ids = list(case.evidence_passage_ids)
    original_records = [
        record.model_dump(mode="json") for record in corpus_passages
    ]

    packet = build_fixed_evidence(case, corpus_passages)

    assert [passage.id for passage in packet.passages] == ids
    assert packet.semantic_passage_ids == ()
    assert packet.additional_graph_passage_ids == ()
    assert case.evidence_passage_ids == original_ids
    assert [
        record.model_dump(mode="json") for record in corpus_passages
    ] == original_records


@pytest.mark.parametrize(
    "passage_id",
    [
        "passage:hegel:wl:being:de",
        "passage:hegel:wl:being:en",
        "passage:kant:groundwork:2:humanity:en",
    ],
)
def test_preserves_exact_text_and_supported_provenance_fields(
    corpus_passages: list[PassageRecord],
    passage_id: str,
) -> None:
    source = next(
        record for record in corpus_passages if record.id == passage_id
    )

    packet = build_fixed_evidence(
        make_case([passage_id]),
        corpus_passages,
    )

    assert asdict(packet.passages[0]) == {
        "id": source.id,
        "text": source.text,
        "source_id": source.source_id,
        "work_id": source.work_id,
        "citation_label": source.citation_label,
        "language": source.language,
        "text_kind": source.text_kind.value,
        "review_status": source.review_status.value,
        "is_verbatim": source.is_verbatim,
        "is_editorial": source.is_editorial,
        "is_machine_generated": source.is_machine_generated,
    }


def test_rejects_unknown_selected_passage(
    corpus_passages: list[PassageRecord],
) -> None:
    case = make_case(["passage:missing"])

    with pytest.raises(ValueError, match="Unknown evidence passage IDs"):
        build_fixed_evidence(case, corpus_passages)


def test_rejects_selection_mutated_to_duplicate_ids(
    corpus_passages: list[PassageRecord],
) -> None:
    passage_id = "passage:hegel:wl:being:de"
    case = make_case([passage_id])
    case.evidence_passage_ids.append(passage_id)

    with pytest.raises(ValueError, match="Duplicate evidence passage ID"):
        build_fixed_evidence(case, corpus_passages)


def test_rejects_selection_mutated_to_empty(
    corpus_passages: list[PassageRecord],
) -> None:
    case = make_case(["passage:hegel:wl:being:de"])
    case.evidence_passage_ids.clear()

    with pytest.raises(ValueError, match="must contain passage IDs"):
        build_fixed_evidence(case, corpus_passages)


@pytest.mark.parametrize(
    "invalid_id",
    ["", "   ", " passage:hegel:wl:being:de "],
)
def test_rejects_selection_mutated_to_invalid_id(
    corpus_passages: list[PassageRecord],
    invalid_id: str,
) -> None:
    case = make_case(["passage:hegel:wl:being:de"])
    case.evidence_passage_ids[0] = invalid_id

    with pytest.raises(ValueError, match="nonblank and trimmed"):
        build_fixed_evidence(case, corpus_passages)


def test_rejects_duplicate_corpus_ids(
    corpus_passages: list[PassageRecord],
) -> None:
    case = make_case(["passage:hegel:wl:being:de"])
    duplicated = [*corpus_passages, corpus_passages[0]]

    with pytest.raises(ValueError, match="Duplicate corpus passage ID"):
        build_fixed_evidence(case, duplicated)


def test_builds_evidence_for_all_repository_cases(
    corpus_passages: list[PassageRecord],
) -> None:
    suite = load_answer_evaluation(
        EVALUATION_DIR / "answer-quality-v1.json",
        CORPUS_DIR,
        EVALUATION_DIR / "semantic-search-v1.json",
    )

    assert len(suite.cases) == 8

    for case in suite.cases:
        packet = build_fixed_evidence(case, corpus_passages)

        assert tuple(passage.id for passage in packet.passages) == tuple(
            case.evidence_passage_ids
        )
        assert packet.semantic_passage_ids == ()
        assert packet.additional_graph_passage_ids == ()
