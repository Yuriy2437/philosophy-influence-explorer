"""Pydantic schemas for semantic Passage search."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PassageConceptResponse(BaseModel):
    """One Concept directly discussed by a semantic search result."""

    id: str
    canonical_label: str
    concept_family: str
    label_en: str
    label_ru: str
    label_de: str


class PassageSearchResult(BaseModel):
    """One semantically retrieved passage returned by the public API."""

    id: str
    text: str
    score: float
    source_id: str
    work_id: str
    citation_label: str
    language: str
    text_kind: str
    is_verbatim: bool
    is_editorial: bool
    is_machine_generated: bool
    concepts: list[PassageConceptResponse]


class PassageSearchResponse(BaseModel):
    """Response body for a semantic passage-search request."""

    query: str
    count: int = Field(ge=0)
    results: list[PassageSearchResult]
