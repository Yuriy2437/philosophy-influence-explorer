"""Top-level API router."""

from fastapi import APIRouter

from philosophy_influence_explorer.api.routes.database import router as database_router
from philosophy_influence_explorer.api.routes.health import router as health_router
from philosophy_influence_explorer.api.routes.passages import router as passages_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(database_router)
api_router.include_router(passages_router)
