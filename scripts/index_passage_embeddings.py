"""Create a vector index and embed curated passages into Neo4j."""

from __future__ import annotations

import argparse

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.embeddings.factory import (
    create_embedding_provider,
)
from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient
from philosophy_influence_explorer.retrieval.passage_indexer import (
    index_curated_passage_embeddings,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line options for passage embedding indexing."""
    parser = argparse.ArgumentParser(
        description="Create a vector index and embed curated Neo4j passages."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate embeddings even when provider/model metadata matches.",
    )
    return parser.parse_args()


def main() -> None:
    """Create the index and persist embeddings for eligible passages."""
    args = parse_args()
    settings = Settings()
    client = Neo4jClient(settings)
    provider = create_embedding_provider(settings)

    try:
        client.verify_connectivity()

        summary = index_curated_passage_embeddings(
            client=client,
            provider=provider,
            batch_size=settings.embedding_batch_size,
            force=args.force,
        )
    finally:
        client.close()

    print(
        "Passage embedding indexing completed: "
        f"eligible={summary.eligible}, "
        f"indexed={summary.indexed}, "
        f"skipped={summary.skipped}, "
        f"provider={provider.model_info.provider}, "
        f"model={provider.model_info.model}, "
        f"dimensions={provider.model_info.dimensions}"
    )


if __name__ == "__main__":
    main()
