"""Controlled indexing of curated Passage embeddings in Neo4j."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from neo4j.exceptions import Neo4jError

from philosophy_influence_explorer.embeddings.base import EmbeddingProvider
from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient

DATASET_ID = "curated_corpus_v1"
PASSAGE_EMBEDDING_INDEX = "passage_embedding_index"


@dataclass(frozen=True)
class PassageForEmbedding:
    """The minimal Passage data needed to create and persist an embedding."""

    id: str
    text: str


@dataclass(frozen=True)
class EmbeddingIndexingSummary:
    """Counts produced by one controlled passage-indexing run."""

    eligible: int
    indexed: int
    skipped: int


def create_passage_embedding_index(
    client: Neo4jClient,
    provider: EmbeddingProvider,
) -> None:
    """Create the Neo4j vector index for the configured embedding dimension."""
    query = f"""
    CREATE VECTOR INDEX {PASSAGE_EMBEDDING_INDEX} IF NOT EXISTS
    FOR (passage:Passage)
    ON (passage.embedding)
    OPTIONS {{
        indexConfig: {{
            `vector.dimensions`: $dimensions,
            `vector.similarity_function`: 'cosine'
        }}
    }}
    """

    try:
        with client.session() as session:
            session.run(
                query,
                dimensions=provider.model_info.dimensions,
            ).consume()
    except Neo4jError as error:
        raise RuntimeError(
            "Unable to create the Passage embedding vector index."
        ) from error


def index_curated_passage_embeddings(
    client: Neo4jClient,
    provider: EmbeddingProvider,
    *,
    batch_size: int,
    force: bool = False,
) -> EmbeddingIndexingSummary:
    """Embed eligible curated passages and write vectors plus model metadata."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1.")

    create_passage_embedding_index(client, provider)

    passages = load_passages_for_embedding(
        client=client,
        provider=provider,
        force=force,
    )

    indexed = 0
    for batch in batched(passages, batch_size):
        vectors = provider.embed_documents([passage.text for passage in batch])

        if len(vectors) != len(batch):
            raise RuntimeError(
                "Embedding provider returned a different number of vectors "
                "than passages in the current batch."
            )

        update_passage_embeddings(
            client=client,
            passages=batch,
            vectors=vectors,
            provider=provider,
        )
        indexed += len(batch)

    return EmbeddingIndexingSummary(
        eligible=len(passages),
        indexed=indexed,
        skipped=0,
    )


def load_passages_for_embedding(
    client: Neo4jClient,
    provider: EmbeddingProvider,
    *,
    force: bool,
) -> list[PassageForEmbedding]:
    """Return deterministic curated passages needing this model's embedding."""
    query = """
    MATCH (passage:Passage {dataset: $dataset_id})
    WHERE $force
       OR passage.embedding IS NULL
       OR passage.embedding_provider <> $provider
       OR passage.embedding_model <> $model
       OR passage.embedding_dimensions <> $dimensions
    RETURN passage.id AS id,
           passage.text AS text
    ORDER BY passage.id
    """

    try:
        with client.session() as session:
            result = session.run(
                query,
                dataset_id=DATASET_ID,
                force=force,
                provider=provider.model_info.provider,
                model=provider.model_info.model,
                dimensions=provider.model_info.dimensions,
            )
            records = list(result)
    except Neo4jError as error:
        raise RuntimeError(
            "Unable to load curated passages for embedding."
        ) from error

    return [
        PassageForEmbedding(
            id=record["id"],
            text=record["text"],
        )
        for record in records
    ]


def update_passage_embeddings(
    client: Neo4jClient,
    passages: Sequence[PassageForEmbedding],
    vectors: Sequence[Sequence[float]],
    provider: EmbeddingProvider,
) -> None:
    """Persist one embedding vector and metadata for each curated Passage."""
    if len(passages) != len(vectors):
        raise ValueError("passages and vectors must have the same length.")

    rows = [
        {
            "id": passage.id,
            "embedding": list(vector),
        }
        for passage, vector in zip(passages, vectors, strict=True)
    ]

    query = """
    UNWIND $rows AS row
    MATCH (passage:Passage {
        id: row.id,
        dataset: $dataset_id
    })
    SET passage.embedding = row.embedding,
        passage.embedding_provider = $provider,
        passage.embedding_model = $model,
        passage.embedding_dimensions = $dimensions,
        passage.embedding_updated_at = $updated_at
    """

    try:
        with client.session() as session:
            session.run(
                query,
                rows=rows,
                dataset_id=DATASET_ID,
                provider=provider.model_info.provider,
                model=provider.model_info.model,
                dimensions=provider.model_info.dimensions,
                updated_at=datetime.now(UTC).isoformat(),
            ).consume()
    except Neo4jError as error:
        raise RuntimeError(
            "Unable to persist Passage embeddings in Neo4j."
        ) from error


def batched(
    values: Sequence[PassageForEmbedding],
    batch_size: int,
) -> Iterator[list[PassageForEmbedding]]:
    """Yield ordered values in batches of at most batch_size."""
    for start in range(0, len(values), batch_size):
        yield list(values[start:start + batch_size])
