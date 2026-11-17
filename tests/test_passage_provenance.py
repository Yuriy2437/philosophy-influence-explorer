"""Offline checks for optional passage acquisition and verification metadata."""

import csv
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from philosophy_influence_explorer.ingestion.models import (
    AcquisitionMethod,
    PassageRecord,
    PreparedBy,
    VerificationStatus,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROVENANCE_FIELDS = (
    "acquisition_method",
    "prepared_by",
    "verification_status",
    "verification_reference",
)


@pytest.fixture
def passage_data() -> dict:
    return {
        "id": "passage:test:provenance",
        "work_id": "work:test",
        "source_id": "source:test",
        "language": "en",
        "text": "Synthetic fixture, not a historical quotation.",
        "text_kind": "editorial_summary",
        "is_verbatim": False,
        "is_machine_generated": False,
        "is_editorial": True,
        "position_label": "Synthetic section",
        "section_order": 1,
        "citation_label": "Synthetic fixture",
        "license_status": "test_fixture",
        "review_status": "reviewed",
    }


def test_legacy_record_gets_unrecorded_defaults(passage_data: dict) -> None:
    record = PassageRecord.model_validate(passage_data)
    assert record.acquisition_method is AcquisitionMethod.NOT_RECORDED
    assert record.prepared_by is PreparedBy.NOT_RECORDED
    assert record.verification_status is VerificationStatus.NOT_RECORDED
    assert record.verification_reference is None


def test_reviewed_primary_quote_does_not_imply_verification(passage_data: dict) -> None:
    passage_data.update(text_kind="primary_quote", is_verbatim=True, is_editorial=False)
    record = PassageRecord.model_validate(passage_data)
    assert record.verification_status is VerificationStatus.NOT_RECORDED
    assert record.prepared_by is PreparedBy.NOT_RECORDED


def test_user_excerpt_is_usable_without_verification(passage_data: dict) -> None:
    passage_data.update(
        acquisition_method="user_excerpt",
        prepared_by="project_author",
        verification_status="not_checked",
    )
    record = PassageRecord.model_validate(passage_data)
    assert record.acquisition_method is AcquisitionMethod.USER_EXCERPT
    assert record.verification_reference is None


@pytest.mark.parametrize("field", PROVENANCE_FIELDS[:3])
def test_unknown_categories_are_rejected(passage_data: dict, field: str) -> None:
    passage_data[field] = "invented_value"
    with pytest.raises(ValidationError):
        PassageRecord.model_validate(passage_data)


@pytest.mark.parametrize("reference", [None, "", "   ", "\t\n"])
def test_checked_status_requires_nonblank_reference(passage_data: dict, reference) -> None:
    passage_data.update(
        verification_status="checked_against_source", verification_reference=reference
    )
    with pytest.raises(ValidationError, match="requires verification_reference"):
        PassageRecord.model_validate(passage_data)


def test_checked_status_preserves_reference_and_other_statuses(passage_data: dict) -> None:
    passage_data.update(
        verification_status="checked_against_source",
        verification_reference="  Synthetic edition, printed p. 7, PDF leaf 9  ",
    )
    record = PassageRecord.model_validate(passage_data)
    assert record.verification_reference == "Synthetic edition, printed p. 7, PDF leaf 9"
    assert record.verification_status is VerificationStatus.CHECKED_AGAINST_SOURCE
    assert record.review_status.value == "reviewed"
    assert record.license_status == "test_fixture"


@pytest.mark.parametrize("blank", ["", "  ", "\t"])
def test_blank_optional_csv_cells_are_unspecified(passage_data: dict, blank: str) -> None:
    passage_data.update(dict.fromkeys(PROVENANCE_FIELDS, blank))
    record = PassageRecord.model_validate(passage_data)
    assert record.acquisition_method is AcquisitionMethod.NOT_RECORDED
    assert record.prepared_by is PreparedBy.NOT_RECORDED
    assert record.verification_status is VerificationStatus.NOT_RECORDED
    assert record.verification_reference is None


def test_reference_alone_does_not_assert_verification(passage_data: dict) -> None:
    passage_data["verification_reference"] = "Possible source, not checked"
    record = PassageRecord.model_validate(passage_data)
    assert record.verification_status is VerificationStatus.NOT_RECORDED


@pytest.mark.parametrize("method", list(AcquisitionMethod))
def test_allowed_acquisition_methods(passage_data: dict, method: AcquisitionMethod) -> None:
    passage_data["acquisition_method"] = method.value
    assert PassageRecord.model_validate(passage_data).acquisition_method is method


@pytest.mark.parametrize("preparer", list(PreparedBy))
def test_allowed_preparers(passage_data: dict, preparer: PreparedBy) -> None:
    passage_data["prepared_by"] = preparer.value
    assert PassageRecord.model_validate(passage_data).prepared_by is preparer


def test_existing_corpus_has_no_inferred_provenance() -> None:
    with (PROJECT_ROOT / "data/curated/passages.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows
    for row in rows:
        record = PassageRecord.model_validate(row)
        for name in PROVENANCE_FIELDS[:3]:
            if name not in row or not row[name].strip():
                assert getattr(record, name).value == "not_recorded"
        if not row.get("verification_reference", "").strip():
            assert record.verification_reference is None


def test_json_schema_matches_model_metadata() -> None:
    schema = json.loads(
        (PROJECT_ROOT / "data/schemas/passage.schema.json").read_text(encoding="utf-8")
    )
    for name, category in (
        ("acquisition_method", AcquisitionMethod),
        ("prepared_by", PreparedBy),
        ("verification_status", VerificationStatus),
    ):
        prop = schema["properties"][name]
        assert set(prop["enum"]) == {member.value for member in category}
        assert prop["default"] == "not_recorded"
        assert name not in schema["required"]
    assert "verification_reference" not in schema["required"]
    assert schema["properties"]["verification_reference"]["default"] is None
    assert any(
        rule.get("if", {}).get("required") == ["verification_status"]
        and rule.get("then", {}).get("required") == ["verification_reference"]
        for rule in schema["allOf"]
    )
