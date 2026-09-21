"""Run a semantic search over curated Passage embeddings."""

from __future__ import annotations

import argparse

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.embeddings.factory import (
    create_embedding_provider,
)
from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageRetriever,
)


def parse_args() -> argparse.Namespace:
    """Parse a semantic query and result limit."""
    parser = argparse.ArgumentParser(
        description="Search curated Neo4j passages by semantic similarity."
    )
    parser.add_argument(
        "query",
        help="Natural-language query to embed and search for.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of passages to return (default: 5).",
    )
    return parser.parse_args()


def main() -> None:
    """Embed a query and print semantically related curated passages."""
    args = parse_args()
    settings = Settings()
    client = Neo4jClient(settings)
    provider = create_embedding_provider(settings)

    try:
        client.verify_connectivity()

        retriever = PassageRetriever(
            client=client,
            provider=provider,
        )
        passages = retriever.search(
            args.query,
            limit=args.limit,
        )
    finally:
        client.close()

    if not passages:
        print("No matching curated passages found.")
        return

    for position, passage in enumerate(passages, start=1):
        print(f"{position}. score={passage.score:.4f}")
        print(f"   id: {passage.id}")
        print(f"   work_id: {passage.work_id}")
        print(f"   source_id: {passage.source_id}")
        print(f"   citation: {passage.citation_label}")
        print(
            "   classification: "
            f"language={passage.language} | "
            f"text_kind={passage.text_kind} | "
            f"verbatim={passage.is_verbatim} | "
            f"editorial={passage.is_editorial} | "
            f"machine_generated={passage.is_machine_generated}"
        )
        print(f"   text: {passage.text}")
        print()


if __name__ == "__main__":
    main()
