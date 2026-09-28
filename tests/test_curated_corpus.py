"""Tests for curated corpus structure, provenance, and cross-file references."""

from pathlib import Path

from philosophy_influence_explorer.ingestion.models import RelationType
from philosophy_influence_explorer.ingestion.validators import validate_curated_corpus

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = PROJECT_ROOT / "data" / "curated"


def test_curated_corpus_validates_successfully() -> None:
    """The version-controlled corpus should satisfy all validation rules."""
    corpus = validate_curated_corpus(CORPUS_DIR)

    assert len(corpus["philosophers"]) == 5
    assert len(corpus["works"]) == 5
    assert len(corpus["concepts"]) == 14
    assert len(corpus["sources"]) == 8
    assert len(corpus["passages"]) == 16
    assert len(corpus["relations"]) == 46


def test_primary_quotes_are_explicitly_marked_as_verbatim() -> None:
    """Primary quotations must not be mistaken for summaries or generated text."""
    corpus = validate_curated_corpus(CORPUS_DIR)

    primary_quotes = [
        passage for passage in corpus["passages"] if passage.text_kind.value == "primary_quote"
    ]

    assert len(primary_quotes) == 7
    assert all(passage.is_verbatim for passage in primary_quotes)
    assert all(not passage.is_editorial for passage in primary_quotes)
    assert all(not passage.is_machine_generated for passage in primary_quotes)


def test_editorial_summaries_are_not_presented_as_translations() -> None:
    """Editorial summaries must be visibly non-verbatim and project-authored."""
    corpus = validate_curated_corpus(CORPUS_DIR)

    summaries = [
        passage for passage in corpus["passages"] if passage.text_kind.value == "editorial_summary"
    ]

    assert summaries
    assert all(not passage.is_verbatim for passage in summaries)
    assert all(passage.is_editorial for passage in summaries)
    assert all(not passage.is_machine_generated for passage in summaries)


def test_conceptual_relations_include_provenance() -> None:
    """Interpretive concept links must retain evidence and review metadata."""
    corpus = validate_curated_corpus(CORPUS_DIR)

    conceptual_relations = [
        relation
        for relation in corpus["relations"]
        if relation.relation_type is RelationType.CONCEPTUALLY_RELATED_TO
    ]

    assert len(conceptual_relations) == 2

    for relation in conceptual_relations:
        properties = relation.properties
        assert properties["evidence_passage_ids"]
        assert properties["evidence_source_ids"]
        assert properties["review_status"] in {"candidate", "reviewed"}


def test_kant_mill_slice_has_explicit_provenance_and_concepts() -> None:
    """New quotations retain source attribution and passage-to-concept links."""
    corpus = validate_curated_corpus(CORPUS_DIR)

    new_passages = {
        passage.id: passage
        for passage in corpus["passages"]
        if passage.id.startswith(("passage:kant:", "passage:mill:"))
    }
    assert len(new_passages) == 4

    expected_concepts = {
        "passage:kant:groundwork:2:autonomy:en": {
            "concept:autonomy",
            "concept:moral-law",
        },
        "passage:kant:groundwork:2:humanity:en": {
            "concept:humanity",
            "concept:end-in-itself",
        },
        "passage:mill:on-liberty:1:harm:en": {
            "concept:liberty",
            "concept:harm-principle",
        },
        "passage:mill:on-liberty:3:individuality:en": {
            "concept:individuality",
            "concept:liberty",
        },
    }

    for passage in new_passages.values():
        assert passage.language == "en"
        assert passage.text_kind.value == "primary_quote"
        assert passage.is_verbatim is True
        assert passage.is_editorial is False
        assert passage.is_machine_generated is False
        assert passage.review_status.value == "candidate"
        assert passage.source_id in {
            "source:kant:gutenberg-5682",
            "source:mill:gutenberg-34901",
        }

    for passage_id, concept_ids in expected_concepts.items():
        actual_concept_ids = {
            relation.to_id
            for relation in corpus["relations"]
            if relation.relation_type is RelationType.DISCUSSES
            and relation.from_id == passage_id
        }
        assert actual_concept_ids == concept_ids
