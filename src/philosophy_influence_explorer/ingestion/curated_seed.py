"""Idempotent loader and scoped reset for curated CSV records in Neo4j."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from neo4j import Driver

from philosophy_influence_explorer.ingestion.models import RelationRecord
from philosophy_influence_explorer.ingestion.validators import validate_curated_corpus

DATASET_ID = "curated_corpus_v1"

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

        merge_passage_languages(session, corpus["passages"])
        merge_translation_links(session, corpus["passages"])

        for relation in corpus["relations"]:
            merge_relation(session, relation)

    return {
        collection_name: len(records)
        for collection_name, records in corpus.items()
    }


def reset_curated_corpus(driver: Driver, database: str) -> None:
    """Delete only nodes and relationships owned by this curated corpus dataset.

    The reset refuses to run when an external relationship points to a curated
    node. This prevents the deletion of an edge owned by another dataset.
    """
    with driver.session(database=database) as session:
        external_relationships = session.run(
            """
            MATCH (node {dataset: $dataset_id})-[relationship]-()
            WHERE relationship.dataset IS NULL
               OR relationship.dataset <> $dataset_id
            RETURN count(relationship) AS count
            """,
            dataset_id=DATASET_ID,
        ).single()["count"]

        if external_relationships:
            raise RuntimeError(
                "Refusing to reset curated corpus because "
                f"{external_relationships} external relationship(s) connect "
                "to curated corpus nodes."
            )

        session.run(
            """
            MATCH ()-[relationship]->()
            WHERE relationship.dataset = $dataset_id
            DELETE relationship
            """,
            dataset_id=DATASET_ID,
        ).consume()

        session.run(
            """
            MATCH (node)
            WHERE node.dataset = $dataset_id
            DELETE node
            """,
            dataset_id=DATASET_ID,
        ).consume()


def merge_nodes(session: Any, label: str, records: Iterable[Any]) -> None:
    """Merge nodes by stable ID and replace their curated properties."""
    query = f"""
    UNWIND $records AS record
    MERGE (node:{label} {{id: record.id}})
    SET node += record,
        node.dataset = $dataset_id
    """

    payload = [
        record.model_dump(mode="json", exclude_none=True)
        for record in records
    ]

    session.run(
        query,
        records=payload,
        dataset_id=DATASET_ID,
    ).consume()


def merge_passage_languages(session: Any, passages: Iterable[Any]) -> None:
    """Create shared Language nodes and dataset-owned language edges."""
    query = """
    UNWIND $passages AS passage
    MERGE (language:Language {code: passage.language})
    ON CREATE SET language.name_en = passage.language
    WITH passage, language
    MATCH (passage_node:Passage {id: passage.id})
    MERGE (passage_node)-[relation:IN_LANGUAGE]->(language)
    SET relation.status = "declared",
        relation.dataset = $dataset_id
    """

    payload = [
        passage.model_dump(mode="json", exclude_none=True)
        for passage in passages
    ]

    session.run(
        query,
        passages=payload,
        dataset_id=DATASET_ID,
    ).consume()


def merge_translation_links(session: Any, passages: Iterable[Any]) -> None:
    """Link summaries/references to the passage they explain or translate."""
    query = """
    UNWIND $passages AS passage
    WITH passage
    WHERE passage.translation_of_passage_id IS NOT NULL
    MATCH (derived:Passage {id: passage.id})
    MATCH (original:Passage {id: passage.translation_of_passage_id})
    MERGE (derived)-[relation:TRANSLATION_OF {
        id: "relation:" + passage.id
            + ":translation-of:"
            + passage.translation_of_passage_id
    }]->(original)
    SET relation.status = CASE
        WHEN passage.text_kind = "editorial_summary" THEN "editorial_summary_of"
        ELSE "translation_reference_of"
    END,
        relation.dataset = $dataset_id
    """

    payload = [
        passage.model_dump(mode="json", exclude_none=True)
        for passage in passages
    ]

    session.run(
        query,
        passages=payload,
        dataset_id=DATASET_ID,
    ).consume()


def merge_relation(session: Any, relation: RelationRecord) -> None:
    """Merge one whitelisted relation with its properties and stable ID."""
    query = f"""
    MATCH (source {{id: $from_id}})
    MATCH (target {{id: $to_id}})
    MERGE (source)-[edge:{relation.relation_type.value} {{id: $id}}]->(target)
    SET edge += $properties,
        edge.review_status = $review_status,
        edge.dataset = $dataset_id
    """

    session.run(
        query,
        id=relation.id,
        from_id=relation.from_id,
        to_id=relation.to_id,
        properties=relation.properties,
        review_status=relation.review_status.value,
        dataset_id=DATASET_ID,
    ).consume()
