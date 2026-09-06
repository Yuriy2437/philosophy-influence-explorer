"""Health-check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from philosophy_influence_explorer import __version__
from philosophy_influence_explorer.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Stable response contract for service health checks."""

    status: str
    service: str
    environment: str
    version: str


@router.get("", response_model=HealthResponse, summary="Check API health")
async def health_check() -> HealthResponse:
    """Return API availability without checking optional dependencies yet."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        version=__version__,
    )
