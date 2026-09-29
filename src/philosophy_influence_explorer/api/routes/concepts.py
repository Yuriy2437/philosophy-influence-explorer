"""Read-only metadata endpoints for curated concepts."""

from fastapi import APIRouter, HTTPException, Request, status
from neo4j.exceptions import Neo4jError
from pydantic import BaseModel

from philosophy_influence_explorer.api.routes.database import get_neo4j_client

router = APIRouter(prefix="/concepts", tags=["concepts"])

_DATASET = "curated_corpus_v1"


class ConceptFamiliesResponse(BaseModel):
    families: list[str]


@router.get(
    "/families",
    response_model=ConceptFamiliesResponse,
    summary="List concept families in the curated corpus",
)
async def list_concept_families(request: Request) -> ConceptFamiliesResponse:
    """Return distinct, non-empty families from curated Concept nodes."""
    query = """
    MATCH (concept:Concept {dataset: $dataset})
    WHERE concept.concept_family IS NOT NULL
      AND trim(concept.concept_family) <> ''
    RETURN DISTINCT concept.concept_family AS family
    ORDER BY family
    """

    client = get_neo4j_client(request)

    try:
        with client.session() as session:
            families = [
                record["family"]
                for record in session.run(query, dataset=_DATASET)
            ]
    except Neo4jError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Concept families are temporarily unavailable.",
        ) from error

    return ConceptFamiliesResponse(families=families)
