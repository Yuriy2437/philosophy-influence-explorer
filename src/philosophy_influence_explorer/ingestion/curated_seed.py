"""Idempotent loader from curated CSV records into Neo4j."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from neo4j import Driver

from philosophy_influence_explorer.ingestion.models import RelationRecord
from philosophy_influence_explorer.ingestion.validators import validate_curated_corpus

NODE_LABELS = {
    "philosophers": "Philosopher",
    "works": "Work",
    "concepts": "Concept",
    "sources": "Source",
    "passages": "Passage",
}


def seed_curated_corpus(
    driver: Driver,
    database: str,
    corpus_dir: Path,
) -> dict[str, int]:
    """Validate and load the curated corpus into Neo4j using MERGE."""
    corpus = validate_curated_corpus(corpus_dir)

    with driver.session(database=database) as session:
        for collection_name, label in NODE_LABELS.items():
            merge_nodes(session, label, corpus[collection_name])

        merge_work_authorship(session, corpus["works"])
        merge_passage_languages(session, corpus["passages"])
        merge_translation_links(session, corpus["passages"])

        for relation in corpus["relations"]:
            merge_relation(session, relation)

    return {collection_name: len(records) for collection_name, records in corpus.items()}


def merge_nodes(session: Any, label: str, records: Iterable[Any]) -> None:
    """Merge nodes by stable ID and replace their curated properties."""
    query = f"""
    UNWIND $records AS record
    MERGE (node:{label} {{id: record.id}})
    SET node += record
    """

    payload = [record.model_dump(mode="json", exclude_none=True) for record in records]
    session.run(query, records=payload).consume()


def merge_work_authorship(session: Any, works: Iterable[Any]) -> None:
    """Create authorship edges from philosopher_id stored on work records."""
    query = """
    UNWIND $works AS work
    MATCH (philosopher:Philosopher {id: work.philosopher_id})
    MATCH (written_work:Work {id: work.id})
    MERGE (philosopher)-[relation:WROTE]->(written_work)
    SET relation.role = "author",
        relation.certainty = 1.0,
        relation.review_status = work.review_status
    """

    payload = [work.model_dump(mode="json") for work in works]
    session.run(query, works=payload).consume()


def merge_passage_languages(session: Any, passages: Iterable[Any]) -> None:
    """Create Language nodes and language edges for each passage."""
    query = """
    UNWIND $passages AS passage
    MERGE (language:Language {code: passage.language})
    ON CREATE SET language.name_en = passage.language
    WITH passage, language
    MATCH (passage_node:Passage {id: passage.id})
    MERGE (passage_node)-[relation:IN_LANGUAGE]->(language)
    SET relation.status = "declared"
    """

    payload = [passage.model_dump(mode="json", exclude_none=True) for passage in passages]
    session.run(query, passages=payload).consume()


def merge_translation_links(session: Any, passages: Iterable[Any]) -> None:
    """Link summaries/references to the passage they explain or translate."""
    query = """
    UNWIND $passages AS passage
    WITH passage
    WHERE passage.translation_of_passage_id IS NOT NULL
    MATCH (derived:Passage {id: passage.id})
    MATCH (original:Passage {id: passage.translation_of_passage_id})
    MERGE (derived)-[relation:TRANSLATION_OF]->(original)
    SET relation.status = CASE
        WHEN passage.text_kind = "editorial_summary" THEN "editorial_summary_of"
        ELSE "translation_reference_of"
    END
    """

    payload = [passage.model_dump(mode="json", exclude_none=True) for passage in passages]
    session.run(query, passages=payload).consume()


def merge_relation(session: Any, relation: RelationRecord) -> None:
    """Merge one whitelisted relation with its properties and stable ID."""
    query = f"""
    MATCH (source {{id: $from_id}})
    MATCH (target {{id: $to_id}})
    MERGE (source)-[edge:{relation.relation_type.value} {{id: $id}}]->(target)
    SET edge += $properties,
        edge.review_status = $review_status
    """

    session.run(
        query,
        id=relation.id,
        from_id=relation.from_id,
        to_id=relation.to_id,
        properties=relation.properties,
        review_status=relation.review_status.value,
    ).consume()
