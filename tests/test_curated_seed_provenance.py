"""Offline seed tests. The fake transaction does not execute Cypher or prove DB rollback."""

from copy import deepcopy
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from philosophy_influence_explorer.ingestion import curated_seed as seed
from philosophy_influence_explorer.ingestion.models import PassageRecord
from philosophy_influence_explorer.ingestion.validators import load_csv_records

FIELDS = (
    "acquisition_method",
    "prepared_by",
    "verification_status",
    "verification_reference",
)
SAVED = {
    "id": "passage:synthetic:seed",
    "acquisition_method": "user_excerpt",
    "prepared_by": "project_author",
    "verification_status": "checked_against_source",
    "verification_reference": "Synthetic edition, printed p. 7",
}


@pytest.fixture
def raw():
    return {
        "id": SAVED["id"],
        "work_id": "work:synthetic",
        "source_id": "source:synthetic",
        "language": "en",
        "text": "Synthetic fixture, not a historical quotation.",
        "text_kind": "editorial_summary",
        "is_verbatim": False,
        "is_machine_generated": False,
        "is_editorial": True,
        "position_label": "Synthetic section",
        "section_order": 1,
        "citation_label": "Synthetic test fixture",
        "license_status": "test_fixture",
        "review_status": "candidate",
    }


def for_seed(raw, **metadata):
    return PassageRecord.model_validate(
        {**raw, **metadata}, context={"passage_seed": True}
    )


class FakeTransaction:
    """Model only the requested property-map semantics, not the Cypher engine."""

    def __init__(self, nodes):
        self.nodes = deepcopy(nodes)
        self.calls = []
        self.markers = []

    def run(self, query, **parameters):
        self.calls.append((query, deepcopy(parameters)))
        assert "UNWIND $rows AS row" in query
        assert "MERGE (node:Passage {id: row.id})" in query
        assert "ON CREATE SET" in query
        assert "SET node += row.record," in query
        assert "node += row.patch" in query
        assert parameters["dataset_id"] == seed.DATASET_ID
        output = []
        for row in parameters["rows"]:
            node = self.nodes.setdefault(
                row["id"],
                {
                    "id": row["id"],
                    "acquisition_method": "not_recorded",
                    "prepared_by": "not_recorded",
                    "verification_status": "not_recorded",
                },
            )
            node.update(row["record"])
            node.update(row["patch"])
            node["dataset"] = parameters["dataset_id"]
            output.append({
                "id": node["id"],
                "verification_status": node.get("verification_status"),
                "verification_reference": node.get("verification_reference"),
            })
        return output


@pytest.mark.parametrize("blank", [None, "", "   ", "\t"])
def test_blank_seed_values_are_not_explicit(raw, blank):
    original = {**raw, **dict.fromkeys(FIELDS, blank)}
    before = deepcopy(original)
    record = PassageRecord.model_validate(original, context={"passage_seed": True})
    assert not set(FIELDS).intersection(record.model_fields_set)
    assert original == before


def test_absent_fields_preserve_saved_values(raw):
    transaction = FakeTransaction({SAVED["id"]: SAVED})
    seed.merge_passages(transaction, [for_seed(raw)])
    node = transaction.nodes[SAVED["id"]]
    assert {name: node[name] for name in FIELDS} == {
        name: SAVED[name] for name in FIELDS
    }
    row = transaction.calls[0][1]["rows"][0]
    assert row["patch"] == {}
    assert not set(FIELDS).intersection(row["record"])


def test_blank_csv_cells_reach_loader_as_omitted_fields(tmp_path, raw):
    import csv

    path = tmp_path / "passages.csv"
    row = {**raw, **dict.fromkeys(FIELDS, "   ")}
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    records = load_csv_records(path, PassageRecord, context={"passage_seed": True})
    transaction = FakeTransaction({SAVED["id"]: SAVED})
    seed.merge_passages(transaction, records)
    assert transaction.calls[0][1]["rows"][0]["patch"] == {}
    assert transaction.nodes[SAVED["id"]]["verification_reference"] == SAVED["verification_reference"]


def test_new_record_gets_defaults_without_reference(raw):
    transaction = FakeTransaction({})
    seed.merge_passages(transaction, [for_seed(raw)])
    node = transaction.nodes[raw["id"]]
    for name in FIELDS[:3]:
        assert node[name] == "not_recorded"
    assert "verification_reference" not in node


def test_explicit_not_recorded_is_an_update(raw):
    saved = {**SAVED, "verification_status": "not_checked"}
    saved.pop("verification_reference")
    transaction = FakeTransaction({SAVED["id"]: saved})
    record = for_seed(raw, verification_status="not_recorded")
    seed.merge_passages(transaction, [record])
    assert transaction.calls[0][1]["rows"][0]["patch"] == {
        "verification_status": "not_recorded"
    }
    assert transaction.nodes[SAVED["id"]]["verification_status"] == "not_recorded"


def test_checked_status_can_reuse_saved_reference(raw):
    transaction = FakeTransaction({SAVED["id"]: SAVED})
    record = for_seed(
        raw, verification_status="checked_against_source", verification_reference=" "
    )
    seed.merge_passages(transaction, [record])
    assert transaction.nodes[SAVED["id"]]["verification_reference"] == SAVED["verification_reference"]
    assert "verification_reference" not in transaction.calls[0][1]["rows"][0]["patch"]


def test_checked_status_without_any_reference_is_rejected(raw):
    transaction = FakeTransaction({})
    record = for_seed(raw, verification_status="checked_against_source")
    with pytest.raises(ValueError, match="requires verification_reference") as error:
        seed.merge_passages(transaction, [record])
    assert raw["id"] in str(error.value)


@pytest.mark.parametrize("status", ["not_recorded", "not_checked"])
def test_new_status_cannot_silently_keep_saved_reference(raw, status):
    transaction = FakeTransaction({SAVED["id"]: SAVED})
    record = for_seed(raw, verification_status=status, verification_reference="")
    with pytest.raises(ValueError, match="conflicts") as error:
        seed.merge_passages(transaction, [record])
    assert raw["id"] in str(error.value)


def test_explicit_reference_updates_saved_reference(raw):
    transaction = FakeTransaction({SAVED["id"]: SAVED})
    seed.merge_passages(transaction, [for_seed(raw, verification_reference="New synthetic p. 8")])
    assert transaction.nodes[SAVED["id"]]["verification_reference"] == "New synthetic p. 8"


def test_regular_validation_still_requires_reference(raw):
    with pytest.raises(ValidationError, match="requires verification_reference"):
        PassageRecord.model_validate({**raw, "verification_status": "checked_against_source"})


@pytest.mark.parametrize("context", [None, {"passage_seed": True}])
def test_seed_context_does_not_disable_other_validation(raw, context):
    with pytest.raises(ValidationError):
        PassageRecord.model_validate({**raw, "prepared_by": "invalid-editor"}, context=context)
    with pytest.raises(ValidationError):
        PassageRecord.model_validate({**raw, "is_verbatim": True}, context=context)


class FakeSession:
    """Expose transaction boundaries without providing session.run()."""

    def __init__(self, nodes):
        self.nodes = deepcopy(nodes)
        self.executions = 0
        self.commits = 0
        self.failures = 0
        self.transaction = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute_write(self, callback):
        self.executions += 1
        self.transaction = FakeTransaction(self.nodes)
        try:
            result = callback(self.transaction)
        except Exception:
            self.failures += 1
            raise
        self.nodes = deepcopy(self.transaction.nodes)
        self.commits += 1
        return result


def setup_seed(monkeypatch, raw, record):
    corpus = {
        "philosophers": [object()],
        "works": [object()],
        "concepts": [object()],
        "sources": [object()],
        "passages": [record],
        "relations": [object()],
    }
    validation_calls = []

    def validate(directory, *, for_seed=False):
        validation_calls.append((directory, for_seed))
        return corpus

    monkeypatch.setattr(seed, "validate_curated_corpus", validate)
    session = FakeSession({SAVED["id"]: SAVED})

    def mark(transaction, label):
        assert transaction is session.transaction
        transaction.markers.append(label)

    monkeypatch.setattr(seed, "merge_nodes", lambda tx, label, records: mark(tx, label))
    monkeypatch.setattr(seed, "merge_passage_languages", lambda tx, records: mark(tx, "languages"))
    monkeypatch.setattr(seed, "merge_translation_links", lambda tx, records: mark(tx, "translations"))
    monkeypatch.setattr(seed, "merge_relation", lambda tx, relation: mark(tx, "relation"))

    def open_session(*, database):
        assert database == "synthetic"
        return session

    return SimpleNamespace(session=open_session), session, corpus, validation_calls


def test_seed_uses_one_transaction_for_all_stages(monkeypatch, raw, tmp_path):
    driver, session, corpus, calls = setup_seed(monkeypatch, raw, for_seed(raw))
    counts = seed.seed_curated_corpus(driver, "synthetic", tmp_path)
    assert calls == [(tmp_path, True)]
    assert session.executions == session.commits == 1
    assert session.failures == 0
    assert session.transaction.markers == [
        "Philosopher", "Work", "Concept", "Source", "languages", "translations", "relation"
    ]
    assert len(session.transaction.calls) == 1
    assert counts == {name: len(records) for name, records in corpus.items()}


def test_conflict_escapes_transaction_callback_and_stops_later_stages(monkeypatch, raw, tmp_path):
    record = for_seed(raw, verification_status="not_recorded")
    driver, session, _, _ = setup_seed(monkeypatch, raw, record)
    before = deepcopy(session.nodes)
    with pytest.raises(ValueError, match="conflicts"):
        seed.seed_curated_corpus(driver, "synthetic", tmp_path)
    assert session.executions == session.failures == 1
    assert session.commits == 0
    assert session.nodes == before
    assert session.transaction.markers == ["Philosopher", "Work", "Concept", "Source"]
