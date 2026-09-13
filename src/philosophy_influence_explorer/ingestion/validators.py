"""CSV loading and cross-file validation for the curated corpus."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import BaseModel, ValidationError

from philosophy_influence_explorer.ingestion.models import (
    ConceptRecord,
    PassageRecord,
    PhilosopherRecord,
    RelationRecord,
    SourceRecord,
    WorkRecord,
)


class CorpusValidationError(ValueError):
    """Raised when curated corpus files violate structural or referential rules."""


def load_csv_records[RecordT: BaseModel](
    file_path: Path,
    model_type: type[RecordT],
) -> list[RecordT]:
    """Read UTF-8 CSV records and validate every row with a Pydantic model."""
    if not file_path.exists():
        raise CorpusValidationError(f"Corpus file does not exist: {file_path}")

    records: list[RecordT] = []

    try:
        with file_path.open(encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise CorpusValidationError(f"CSV file has no header: {file_path}")

            for row_number, row in enumerate(reader, start=2):
                try:
                    records.append(model_type.model_validate(row))
                except ValidationError as error:
                    raise CorpusValidationError(
                        f"{file_path.name}, row {row_number}: {error}"
                    ) from error
    except UnicodeDecodeError as error:
        raise CorpusValidationError(f"{file_path.name} must use UTF-8 encoding.") from error

    ensure_unique_ids(records, file_path.name)
    return records


def ensure_unique_ids(records: list[BaseModel], file_name: str) -> None:
    """Reject duplicate stable identifiers within one CSV file."""
    identifiers = [record.id for record in records]
    duplicates = sorted(
        identifier for identifier in set(identifiers) if identifiers.count(identifier) > 1
    )

    if duplicates:
        raise CorpusValidationError(f"{file_name} contains duplicate IDs: {', '.join(duplicates)}")


def validate_curated_corpus(corpus_dir: Path) -> dict[str, list[BaseModel]]:
    """Load all curated CSV files and validate cross-file references."""
    philosophers = load_csv_records(
        corpus_dir / "philosophers.csv",
        PhilosopherRecord,
    )
    works = load_csv_records(corpus_dir / "works.csv", WorkRecord)
    concepts = load_csv_records(corpus_dir / "concepts.csv", ConceptRecord)
    sources = load_csv_records(corpus_dir / "sources.csv", SourceRecord)
    passages = load_csv_records(corpus_dir / "passages.csv", PassageRecord)
    relations = load_csv_records(corpus_dir / "relations.csv", RelationRecord)

    all_ids = {
        record.id
        for collection in [philosophers, works, concepts, sources, passages]
        for record in collection
    }

    validate_work_references(works, philosopher_ids={record.id for record in philosophers})
    validate_work_sources(works, source_ids={record.id for record in sources})
    validate_passage_references(
        passages,
        work_ids={record.id for record in works},
        source_ids={record.id for record in sources},
    )
    validate_translation_references(passages)
    validate_relation_references(relations, all_ids)

    return {
        "philosophers": philosophers,
        "works": works,
        "concepts": concepts,
        "sources": sources,
        "passages": passages,
        "relations": relations,
    }


def validate_work_references(
    works: list[WorkRecord],
    philosopher_ids: set[str],
) -> None:
    """Ensure every work belongs to a known philosopher."""
    for work in works:
        if work.philosopher_id not in philosopher_ids:
            raise CorpusValidationError(
                f"{work.id} references unknown philosopher: {work.philosopher_id}"
            )


def validate_work_sources(
    works: list[WorkRecord],
    source_ids: set[str],
) -> None:
    """Ensure every work points to a known source record."""
    for work in works:
        if work.source_id not in source_ids:
            raise CorpusValidationError(f"{work.id} references unknown source: {work.source_id}")


def validate_passage_references(
    passages: list[PassageRecord],
    work_ids: set[str],
    source_ids: set[str],
) -> None:
    """Ensure every passage points to known work and source records."""
    for passage in passages:
        if passage.work_id not in work_ids:
            raise CorpusValidationError(f"{passage.id} references unknown work: {passage.work_id}")
        if passage.source_id not in source_ids:
            raise CorpusValidationError(
                f"{passage.id} references unknown source: {passage.source_id}"
            )


def validate_translation_references(passages: list[PassageRecord]) -> None:
    """Ensure optional translation references point to existing passages."""
    passage_ids = {passage.id for passage in passages}

    for passage in passages:
        translation_of = passage.translation_of_passage_id
        if translation_of is not None and translation_of not in passage_ids:
            raise CorpusValidationError(
                f"{passage.id} references unknown passage: {translation_of}"
            )


def validate_relation_references(
    relations: list[RelationRecord],
    all_ids: set[str],
) -> None:
    """Ensure each relation points to graph entities present in this corpus."""
    for relation in relations:
        if relation.from_id not in all_ids:
            raise CorpusValidationError(f"{relation.id} has unknown from_id: {relation.from_id}")
        if relation.to_id not in all_ids:
            raise CorpusValidationError(f"{relation.id} has unknown to_id: {relation.to_id}")
