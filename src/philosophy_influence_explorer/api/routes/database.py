"""Database health and graph-summary endpoints."""

from fastapi import APIRouter, HTTPException, Request, status
from neo4j.exceptions import DriverError, Neo4jError
from pydantic import BaseModel

from philosophy_influence_explorer.api.dependencies import get_neo4j_client

router = APIRouter(prefix="/health/database", tags=["health"])


class DatabaseHealthResponse(BaseModel):
    """Stable response contract for Neo4j connectivity health checks."""

    status: str
    database: str


class GraphSummaryResponse(BaseModel):
    """Basic graph size information."""

    total_nodes: int
    total_relationships: int


@router.get("", response_model=DatabaseHealthResponse, summary="Check Neo4j connectivity")
async def database_health_check(request: Request) -> DatabaseHealthResponse:
    """Verify that the API can authenticate and connect to Neo4j."""
    client = get_neo4j_client(request)

    try:
        client.verify_connectivity()
    except (DriverError, Neo4jError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is temporarily unavailable.",
        ) from error

    return DatabaseHealthResponse(
        status="ok",
        database=request.app.state.neo4j_database,
    )


@router.get(
    "/summary",
    response_model=GraphSummaryResponse,
    summary="Return basic graph statistics",
)
async def graph_summary(request: Request) -> GraphSummaryResponse:
    """Return total node and relationship counts in the current graph."""
    client = get_neo4j_client(request)

    try:
        summary = client.get_graph_summary()
    except (DriverError, Neo4jError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph summary is temporarily unavailable.",
        ) from error

    return GraphSummaryResponse(**summary)
