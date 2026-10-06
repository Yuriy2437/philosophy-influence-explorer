"""FastAPI dependencies for application services."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from philosophy_influence_explorer.config import get_settings
from philosophy_influence_explorer.embeddings.factory import (
    create_embedding_provider,
)
from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageRetriever,
)


def get_neo4j_client(request: Request) -> Neo4jClient:
    """Return the active client or report database unavailability."""
    client = getattr(request.app.state, "neo4j_client", None)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable.",
        )

    return client


def get_passage_retriever(request: Request) -> PassageRetriever:
    """Build a semantic retriever only when the database is available."""
    client = get_neo4j_client(request)
    settings = get_settings()
    provider = create_embedding_provider(settings)

    return PassageRetriever(
        client=client,
        provider=provider,
    )
