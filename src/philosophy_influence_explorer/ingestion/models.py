"""Typed models for curated CSV corpus records."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ReviewStatus(StrEnum):
    """Editorial status used to control user-facing corpus data."""

    CURATED = "curated"
    REVIEWED = "reviewed"
    CANDIDATE = "candidate"
    REJECTED = "rejected"


class PassageKind(StrEnum):
    """Allowed text provenance categories."""

    PRIMARY_QUOTE = "primary_quote"
    EDITORIAL_SUMMARY = "editorial_summary"
    BIBLIOGRAPHIC_NOTE = "bibliographic_note"
    TRANSLATION_REFERENCE = "translation_reference"


class RelationType(StrEnum):
    """Allowed relation types in the curated MVP corpus."""

    WROTE = "WROTE"
    HAS_PASSAGE = "HAS_PASSAGE"
    DISCUSSES = "DISCUSSES"
    CONCEPTUALLY_RELATED_TO = "CONCEPTUALLY_RELATED_TO"


class CsvRecord(BaseModel):
    """Base model that rejects accidental columns in curated CSV files."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PhilosopherRecord(CsvRecord):
    """A philosopher node from philosophers.csv."""

    id: str = Field(pattern=r"^philosopher:")
    canonical_name: str = Field(min_length=1)
    name_en: str = Field(min_length=1)
    name_ru: str = Field(min_length=1)
    name_de: str = Field(min_length=1)
    birth_year: int
    death_year: int
    bio_note: str = Field(min_length=1)
    review_status: ReviewStatus


class WorkRecord(CsvRecord):
    """A work node from works.csv."""

    id: str = Field(pattern=r"^work:")
    philosopher_id: str = Field(pattern=r"^philosopher:")
    title: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    title_ru: str = Field(min_length=1)
    title_de: str = Field(min_length=1)
    original_language: str = Field(pattern=r"^(ru|en|de|la)$")
    publication_year: int
    work_kind: str = Field(min_length=1)
    is_translation: bool
    source_id: str = Field(pattern=r"^source:")
    license_status: str = Field(min_length=1)
    review_status: ReviewStatus


class ConceptRecord(CsvRecord):
    """A controlled concept node from concepts.csv."""

    id: str = Field(pattern=r"^concept:")
    canonical_label: str = Field(min_length=1)
    label_en: str = Field(min_length=1)
    label_ru: str = Field(min_length=1)
    label_de: str = Field(min_length=1)
    description: str = Field(min_length=1)
    concept_family: str = Field(min_length=1)
    review_status: ReviewStatus


class SourceRecord(CsvRecord):
    """A bibliographic/provenance source node from sources.csv."""

    id: str = Field(pattern=r"^source:")
    citation_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    authors: str = Field(min_length=1)
    publication_year: int
    source_type: str = Field(min_length=1)
    url: str = ""
    license_status: str = Field(min_length=1)
    access_note: str = Field(min_length=1)
    review_status: ReviewStatus


class PassageRecord(CsvRecord):
    """A citable passage, editorial summary, or bibliographic note."""

    id: str = Field(pattern=r"^passage:")
    work_id: str = Field(pattern=r"^work:")
    source_id: str = Field(pattern=r"^source:")
    language: str = Field(pattern=r"^(ru|en|de|la)$")
    text: str = Field(min_length=1)
    text_kind: PassageKind
    is_verbatim: bool
    is_machine_generated: bool
    is_editorial: bool
    translation_of_passage_id: str | None = None
    position_label: str = Field(min_length=1)
    section_order: int = Field(ge=1)
    citation_label: str = Field(min_length=1)
    license_status: str = Field(min_length=1)
    review_status: ReviewStatus

    @field_validator("translation_of_passage_id", mode="before")
    @classmethod
    def empty_translation_reference_is_none(cls, value: object) -> object:
        """Normalize an empty CSV cell to None."""
        return None if value == "" else value

    @model_validator(mode="after")
    def validate_text_provenance(self) -> PassageRecord:
        """Enforce transparent distinctions between quotes and editorial text."""
        if self.text_kind is PassageKind.PRIMARY_QUOTE:
            if not self.is_verbatim or self.is_editorial:
                raise ValueError("primary_quote must have is_verbatim=true and is_editorial=false.")

        if self.text_kind is PassageKind.EDITORIAL_SUMMARY:
            if self.is_verbatim or not self.is_editorial:
                raise ValueError(
                    "editorial_summary must have is_verbatim=false and is_editorial=true."
                )

        return self


class RelationRecord(CsvRecord):
    """A graph relation from relations.csv with validated JSON properties."""

    id: str = Field(pattern=r"^relation:")
    relation_type: RelationType
    from_id: str = Field(min_length=1)
    to_id: str = Field(min_length=1)
    properties_json: str = Field(min_length=2)
    review_status: ReviewStatus

    @property
    def properties(self) -> dict[str, Any]:
        """Decode the JSON object stored in the CSV column."""
        decoded = json.loads(self.properties_json)
        if not isinstance(decoded, dict):
            raise ValueError("properties_json must decode to a JSON object.")
        return decoded

    @model_validator(mode="after")
    def validate_scholarly_claim_provenance(self) -> RelationRecord:
        """Require explicit provenance fields on interpretive relations."""
        if self.relation_type is RelationType.CONCEPTUALLY_RELATED_TO:
            properties = self.properties
            required = {
                "relation_type",
                "asserted_by",
                "evidence_passage_ids",
                "evidence_source_ids",
                "claim_language",
                "confidence",
                "review_status",
                "created_at",
                "updated_at",
            }
            missing = sorted(required.difference(properties))
            if missing:
                raise ValueError(
                    "CONCEPTUALLY_RELATED_TO is missing provenance fields: " + ", ".join(missing)
                )

        return self
