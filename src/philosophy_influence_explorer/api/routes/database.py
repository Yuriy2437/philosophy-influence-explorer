"""Database health and graph-summary endpoints."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient

router = APIRouter(prefix="/health/database", tags=["health"])


class DatabaseHealthResponse(BaseModel):
    """Stable response contract for Neo4j connectivity health checks."""

    status: str
    database: str


class GraphSummaryResponse(BaseModel):
    """Basic graph size information for local development."""

    total_nodes: int
    total_relationships: int


def get_neo4j_client(request: Request) -> Neo4jClient:
    """Retrieve the application-owned Neo4j client."""
    return request.app.state.neo4j_client


@router.get("", response_model=DatabaseHealthResponse, summary="Check Neo4j connectivity")
async def database_health_check(request: Request) -> DatabaseHealthResponse:
    """Verify that the API can authenticate and connect to Neo4j."""
    client = get_neo4j_client(request)
    client.verify_connectivity()
    return DatabaseHealthResponse(status="ok", database=request.app.state.neo4j_database)


@router.get(
    "/summary",
    response_model=GraphSummaryResponse,
    summary="Return basic graph statistics",
)
async def graph_summary(request: Request) -> GraphSummaryResponse:
    """Return total node and relationship counts in the current graph."""
    client = get_neo4j_client(request)
    return GraphSummaryResponse(**client.get_graph_summary())
