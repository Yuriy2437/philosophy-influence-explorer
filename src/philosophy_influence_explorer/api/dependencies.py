"""FastAPI dependencies for application services."""

from __future__ import annotations

from fastapi import Request

from philosophy_influence_explorer.config import get_settings
from philosophy_influence_explorer.embeddings.factory import (
    create_embedding_provider,
)
from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageRetriever,
)


def get_neo4j_client(request: Request) -> Neo4jClient:
    """Return the Neo4j client owned by the application lifespan."""
    return request.app.state.neo4j_client


def get_passage_retriever(request: Request) -> PassageRetriever:
    """Build a semantic Passage retriever for the active application."""
    settings = get_settings()
    provider = create_embedding_provider(settings)

    return PassageRetriever(
        client=get_neo4j_client(request),
        provider=provider,
    )
