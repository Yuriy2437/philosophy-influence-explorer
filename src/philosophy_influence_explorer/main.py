"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from philosophy_influence_explorer import __version__
from philosophy_influence_explorer.api.router import api_router
from philosophy_influence_explorer.config import get_settings
from philosophy_influence_explorer.graph.neo4j_client import Neo4jClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create and close infrastructure clients with the app lifecycle."""
    settings = get_settings()
    neo4j_client = Neo4jClient(settings)

    app.state.neo4j_client = neo4j_client
    app.state.neo4j_database = settings.neo4j_database

    try:
        yield
    finally:
        neo4j_client.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "A multilingual, source-grounded GraphRAG API for exploring "
            "philosophical concepts and intellectual influence."
        ),
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", tags=["service"])
    async def root() -> dict[str, str]:
        """Return minimal service metadata."""
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/health",
            "database_health": f"{settings.api_v1_prefix}/health/database",
            "graph_summary": f"{settings.api_v1_prefix}/health/database/summary",
        }

    return app


app = create_app()
