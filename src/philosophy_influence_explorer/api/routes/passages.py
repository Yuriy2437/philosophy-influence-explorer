"""Semantic search endpoints for curated Passage nodes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from philosophy_influence_explorer.api.dependencies import (
    get_passage_retriever,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageSearchFilters,
    PassageRetriever,
)
from philosophy_influence_explorer.schemas.passages import (
    PassageConceptResponse,
    PassageSearchResponse,
    PassageSearchResult,
)

router = APIRouter(prefix="/passages", tags=["passages"])


@router.get(
    "/search",
    response_model=PassageSearchResponse,
    summary="Search curated passages by semantic similarity",
)
async def search_passages(
    q: Annotated[
        str,
        Query(
            min_length=1,
            description="Natural-language semantic search query.",
        ),
    ],
    retriever: Annotated[
        PassageRetriever,
        Depends(get_passage_retriever),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=20,
            description="Maximum number of passages to return.",
        ),
    ] = 5,
    concept_family: Annotated[
        str | None,
        Query(
            description=(
                "Restrict results to passages that discuss a Concept in "
                "this family, for example: dialectic, epistemology, "
                "metaphysics, or ontology."
            ),
        ),
    ] = None,
    language: Annotated[
        str | None,
        Query(
            description=(
                "Restrict results by Passage language code, for example: "
                "en, ru, de, or la."
            ),
        ),
    ] = None,
    is_verbatim: Annotated[
        bool | None,
        Query(
            description=(
                "Restrict results to verbatim primary texts (true) or "
                "non-verbatim project material (false)."
            ),
        ),
    ] = None,
    is_editorial: Annotated[
        bool | None,
        Query(
            description=(
                "Restrict results to editorial material (true) or "
                "non-editorial material (false)."
            ),
        ),
    ] = None,
) -> JSONResponse:
    """Embed a query and retrieve filtered curated passages."""
    normalized_query = q.strip()

    if not normalized_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' must not be blank.",
        )

    filters = PassageSearchFilters(
        concept_family=concept_family,
        language=language,
        is_verbatim=is_verbatim,
        is_editorial=is_editorial,
    )

    try:
        passages = retriever.search(
            normalized_query,
            limit=limit,
            filters=filters,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic search service is temporarily unavailable.",
        ) from error

    results = [
        PassageSearchResult(
            id=passage.id,
            text=passage.text,
            score=passage.score,
            source_id=passage.source_id,
            work_id=passage.work_id,
            citation_label=passage.citation_label,
            language=passage.language,
            text_kind=passage.text_kind,
            is_verbatim=passage.is_verbatim,
            is_editorial=passage.is_editorial,
            is_machine_generated=passage.is_machine_generated,
            concepts=[
                PassageConceptResponse(
                    id=concept.id,
                    canonical_label=concept.canonical_label,
                    concept_family=concept.concept_family,
                    label_en=concept.label_en,
                    label_ru=concept.label_ru,
                    label_de=concept.label_de,
                )
                for concept in passage.concepts
            ],
        )
        for passage in passages
    ]

    payload = PassageSearchResponse(
        query=normalized_query,
        count=len(results),
        results=results,
    )

    return JSONResponse(
        content=payload.model_dump(),
        media_type="application/json; charset=utf-8",
    )
