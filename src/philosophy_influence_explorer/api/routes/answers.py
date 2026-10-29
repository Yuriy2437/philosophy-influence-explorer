"""Operator-only evidence-grounded answer endpoint."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from philosophy_influence_explorer.api.dependencies import (
    get_semantic_graph_retriever,
)
from philosophy_influence_explorer.api.generation_access import (
    require_generation_access,
)
from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.generation.gemini import (
    GeminiAnswerGenerator,
    GeminiAnswerGeneratorError,
)
from philosophy_influence_explorer.retrieval.passage_retriever import (
    PassageSearchFilters,
)
from philosophy_influence_explorer.schemas.answers import (
    AnswerEvidencePassage,
    AnswerEvidenceResponse,
    AnswerRequest,
    AnswerResponse,
)
from philosophy_influence_explorer.workflows.answer_workflow import (
    build_answer_workflow,
)

router = APIRouter(prefix="/answers", tags=["answers"])


def build_operator_answer_workflow(request: Request, settings: Settings):
    """Create services only after the route's access gate has approved."""
    key = settings.google_api_key

    if key is None or not key.get_secret_value().strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation service is unavailable.",
        )

    try:
        generator = GeminiAnswerGenerator(
            api_key=key.get_secret_value(),
            model=settings.generation_model,
            timeout_seconds=settings.generation_timeout_seconds,
        )
        retriever = get_semantic_graph_retriever(request)
        return build_answer_workflow(retriever, generator)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation service is unavailable.",
        ) from None
    except (ValueError, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation service is unavailable.",
        ) from None


@router.post(
    "",
    response_model=AnswerResponse,
    summary="Generate an evidence-grounded answer with operator access",
    responses={
        401: {"description": "Operator access is missing or invalid."},
        502: {"description": "An acceptable answer could not be produced."},
        503: {"description": "Generation or retrieval is unavailable."},
    },
)
def answer_post(
    request: Request,
    body: AnswerRequest,
    settings: Annotated[Settings, Depends(require_generation_access)],
) -> JSONResponse:
    """Run one answer workflow without automatic retries."""
    workflow = build_operator_answer_workflow(request, settings)

    try:
        state = workflow.invoke(
            {
                "query_text": body.q,
                "limit": body.limit,
                "graph_limit": body.graph_limit,
                "filters": PassageSearchFilters(
                    concept_family=body.concept_family,
                    language=body.language,
                    is_verbatim=body.is_verbatim,
                    is_editorial=body.is_editorial,
                ),
            }
        )

        packet = state["evidence"]
        payload = AnswerResponse(
            query=state["query_text"],
            answer=state["answer"],
            evidence=AnswerEvidenceResponse(
                passages=[
                    AnswerEvidencePassage.model_validate(asdict(passage))
                    for passage in packet.passages
                ],
                semantic_passage_ids=list(packet.semantic_passage_ids),
                additional_graph_passage_ids=list(
                    packet.additional_graph_passage_ids
                ),
            ),
        )
    except GeminiAnswerGeneratorError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="An acceptable answer could not be produced.",
        ) from None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Answer workflow validation failed.",
        ) from None
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation service is temporarily unavailable.",
        ) from None

    return JSONResponse(
        content=payload.model_dump(mode="json"),
        media_type="application/json; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )
