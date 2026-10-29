"""Access gate for operator-only answer generation."""

from __future__ import annotations

from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from philosophy_influence_explorer.config import Settings, get_settings

generation_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="GenerationOperatorToken",
)


def require_generation_access(
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(generation_bearer),
    ],
) -> Settings:
    """Reject disabled or unauthorized requests without creating services."""
    if not settings.generation_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation is unavailable.",
        )

    configured = settings.generation_access_token
    expected = configured.get_secret_value() if configured is not None else ""

    if not expected.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation is unavailable.",
        )

    supplied = credentials.credentials if credentials is not None else ""

    if not compare_digest(
        supplied.encode("utf-8"),
        expected.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Generation access denied.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return settings
