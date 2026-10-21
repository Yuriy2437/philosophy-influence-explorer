"""Retrieval-only query endpoint with explicit graph context."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from philosophy_influence_explorer.api.dependencies import (
    get_semantic_graph_retriever,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageSearchFilters,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphRetriever,
)
from philosophy_influence_explorer.schemas.passages import (
    PassageConceptResponse,
    PassageSearchResult,
)

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    """Validated retrieval-only query body."""

    q: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)
    graph_limit: int = Field(default=20, ge=1, le=20)
    concept_family: str | None = None
    language: str | None = None
    is_verbatim: bool | None = None
    is_editorial: bool | None = None


class GraphEdgeResponse(BaseModel):
    """A directed graph edge, not a claim of historical influence."""

    id: str
    from_id: str
    to_id: str
    review_status: str
    extraction_method: str | None
    confidence: float | None
    relation_type: Literal["DISCUSSES"]


class GraphPassageResponse(BaseModel):
    """Graph-derived passage without a vector similarity score."""

    id: str
    text: str
    source_id: str
    work_id: str
    citation_label: str
    language: str
    text_kind: str
    review_status: str
    is_verbatim: bool
    is_editorial: bool
    is_machine_generated: bool


class GraphPathResponse(BaseModel):
    """One seed -> concept <- related passage path."""

    seed_id: str
    concept: PassageConceptResponse
    seed_edge: GraphEdgeResponse
    related_edge: GraphEdgeResponse
    passage: GraphPassageResponse


class QueryResponse(BaseModel):
    """Keep semantic matches and graph paths separate."""

    query: str
    mode: Literal["retrieval_only"] = "retrieval_only"
    semantic_count: int = Field(ge=0)
    graph_path_count: int = Field(ge=0)
    semantic_passages: list[PassageSearchResult]
    graph_context: list[GraphPathResponse]


@router.post(
    "",
    response_model=QueryResponse,
    summary="Retrieve passages and graph context without generating an answer",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Blank query or invalid retrieval input.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Retrieval infrastructure is unavailable.",
        },
    },
)
def query_post(
    body: QueryRequest,
    retriever: Annotated[
        SemanticGraphRetriever,
        Depends(get_semantic_graph_retriever),
    ],
) -> JSONResponse:
    """Run the synchronous retrieval service using a validated POST body."""
    normalized_query = body.q.strip()

    if not normalized_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' must not be blank.",
        )

    filters = PassageSearchFilters(
        concept_family=body.concept_family,
        language=body.language,
        is_verbatim=body.is_verbatim,
        is_editorial=body.is_editorial,
    )

    try:
        result = retriever.retrieve(
            normalized_query,
            limit=body.limit,
            graph_limit=body.graph_limit,
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
            detail="Query retrieval service is temporarily unavailable.",
        ) from error

    payload = QueryResponse(
        query=normalized_query,
        semantic_count=len(result.semantic_passages),
        graph_path_count=len(result.graph_context),
        semantic_passages=[
            PassageSearchResult.model_validate(asdict(passage))
            for passage in result.semantic_passages
        ],
        graph_context=[
            GraphPathResponse.model_validate(asdict(path))
            for path in result.graph_context
        ],
    )

    return JSONResponse(
        content=payload.model_dump(mode="json"),
        media_type="application/json; charset=utf-8",
    )
