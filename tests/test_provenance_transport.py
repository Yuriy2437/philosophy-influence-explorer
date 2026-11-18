"""Offline provenance transport tests; all service calls are replaced by fakes."""

from dataclasses import asdict, replace
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from philosophy_influence_explorer.evaluation.answer_evidence import build_fixed_evidence
from philosophy_influence_explorer.generation.gemini import (
    GeminiAnswerGenerator,
    GeminiAnswerGeneratorError,
)
from philosophy_influence_explorer.ingestion.models import PassageRecord
from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextRetriever,
)
from philosophy_influence_explorer.retrieval.passage_retriever import PassageRetriever
from philosophy_influence_explorer.workflows.evidence import prepare_evidence
from tests import test_graph_context_retriever as graph_tests
from tests import test_passage_retriever as passage_tests
from tests import test_passage_search_api as search_tests
from tests import test_query_api as query_tests
from tests import test_workflow_evidence as evidence_tests
from tests.test_answer_api import authorization, setup_api as setup_api
from tests.test_answer_evaluation_evidence import make_case

META = {
    "acquisition_method": "user_excerpt",
    "prepared_by": "project_author",
    "verification_status": "checked_against_source",
    "verification_reference": "Synthetic edition, section 2, printed p. 7",
}
DEFAULTS = {
    "acquisition_method": "not_recorded",
    "prepared_by": "not_recorded",
    "verification_status": "not_recorded",
    "verification_reference": None,
}


def assert_metadata(data: dict, expected: dict) -> None:
    assert {name: data[name] for name in expected} == expected


@pytest.mark.parametrize("metadata", [META, {}, dict.fromkeys(META)])
def test_semantic_retrieval_metadata(metadata: dict) -> None:
    row = passage_tests._record()
    row.update(metadata)
    client = passage_tests.FakeClient([row])
    result = PassageRetriever(
        client=client, provider=passage_tests.FakeProvider()
    ).search("freedom and morality")
    assert_metadata(asdict(result[0]), META if metadata == META else DEFAULTS)
    query = client.fake_session.calls[0][0]
    for name in META:
        assert f"node.{name}" in query
    assert "coalesce(node.verification_status, 'not_recorded')" in query


@pytest.mark.parametrize("metadata", [META, {}])
def test_graph_retrieval_metadata(metadata: dict) -> None:
    row = graph_tests._record()
    row["passage"].update(metadata)
    client = graph_tests.FakeClient([row])
    result = GraphContextRetriever(client=client).expand([row["seed_id"]])
    assert_metadata(asdict(result[0].passage), META if metadata else DEFAULTS)
    query = client.fake_session.calls[0][0]
    for name in META:
        assert f"related.{name}" in query or f".{name}" in query
    assert "coalesce(related.verification_status, 'not_recorded')" in query
    assert not hasattr(result[0].passage, "score")


def enriched_result():
    result = query_tests._result()
    seed = replace(result.semantic_passages[0], **META)
    path = result.graph_context[0]
    related = replace(path.passage, **META)
    return replace(
        result,
        semantic_passages=(seed,),
        graph_context=(replace(path, passage=related),),
    )


def test_evidence_preserves_both_retrieval_paths() -> None:
    result = enriched_result()
    packet = prepare_evidence(result)
    assert len(packet.passages) == 2
    assert packet.semantic_passage_ids == (result.semantic_passages[0].id,)
    assert packet.additional_graph_passage_ids == (result.graph_context[0].passage.id,)
    for record in packet.passages:
        assert_metadata(asdict(record), META)


@pytest.mark.parametrize("field", list(META))
def test_evidence_rejects_conflicting_metadata(field: str) -> None:
    record = replace(evidence_tests.passage("passage:transport"), **META)
    conflicting = replace(record, **{field: "different"})
    result = query_tests.SemanticGraphResult(
        (evidence_tests.semantic(record),),
        (evidence_tests.path(record.id, conflicting),),
    )
    with pytest.raises(ValueError, match="Conflicting evidence records"):
        prepare_evidence(result)


@pytest.mark.parametrize("method", ["get", "post"])
def test_passage_search_api_preserves_metadata(method: str) -> None:
    record = replace(search_tests._passage(), **META)
    retriever = search_tests.FakePassageRetriever(passages=[record])
    with search_tests.make_client(retriever) as client:
        if method == "get":
            response = client.get("/api/v1/passages/search", params={"q": "synthetic"})
        else:
            response = client.post("/api/v1/passages/search", json={"q": "synthetic"})
    assert response.status_code == 200
    assert_metadata(response.json()["results"][0], META)


def test_query_api_preserves_both_paths() -> None:
    retriever = query_tests.FakeQueryRetriever(result=enriched_result())
    with query_tests.make_client(retriever) as client:
        response = client.post("/api/v1/query", json={"q": "synthetic"})
    assert response.status_code == 200
    payload = response.json()
    assert_metadata(payload["semantic_passages"][0], META)
    assert_metadata(payload["graph_context"][0]["passage"], META)


def test_answer_api_preserves_evidence_metadata(setup_api) -> None:
    app, _, retriever, generator, _, _ = setup_api
    retriever.retrieve.return_value = enriched_result()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            headers=authorization(),
            json={"q": "Synthetic question"},
        )
    assert response.status_code == 200
    for record in response.json()["evidence"]["passages"]:
        assert_metadata(record, META)
    for record in generator.generate.call_args.kwargs["evidence"].passages:
        assert_metadata(asdict(record), META)


def test_generation_serializes_metadata_without_live_http(monkeypatch) -> None:
    captured = {}
    encode_json = json.dumps

    def fake_post(url, *, headers, json, timeout):
        captured.update(json)
        answer = {
            "status": "insufficient_evidence",
            "claims": [],
            "limitations": ["Synthetic fixture only."],
        }
        return httpx.Response(
            200,
            request=httpx.Request("POST", "https://example.test"),
            json={"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": encode_json(answer)}]},
            }]},
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    generator = GeminiAnswerGenerator(api_key="test-key", model="test-model")
    generator.generate(query_text="Synthetic", evidence=prepare_evidence(enriched_result()))
    payload = json.loads(captured["contents"][0]["parts"][0]["text"])
    for record in payload["passages"]:
        assert_metadata(record, META)


def test_fixed_evidence_preserves_explicit_metadata() -> None:
    record = PassageRecord.model_validate({
        "id": "passage:synthetic:fixed",
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
        "citation_label": "Synthetic fixture",
        "license_status": "test_fixture",
        "review_status": "candidate",
        **META,
    })
    packet = build_fixed_evidence(make_case([record.id]), [record])
    assert_metadata(asdict(packet.passages[0]), META)
    assert packet.semantic_passage_ids == ()
    assert packet.additional_graph_passage_ids == ()


def test_large_verification_reference_obeys_existing_input_budget(monkeypatch) -> None:
    def deny_http(*args, **kwargs):
        raise AssertionError("No HTTP call is allowed for oversized evidence.")

    monkeypatch.setattr(httpx, "post", deny_http)
    result = enriched_result()
    seed = replace(result.semantic_passages[0], verification_reference="x" * 65_000)
    result = replace(result, semantic_passages=(seed,))
    generator = GeminiAnswerGenerator(api_key="test-key", model="test-model")
    with pytest.raises(GeminiAnswerGeneratorError, match="byte budget"):
        generator.generate(query_text="Synthetic", evidence=prepare_evidence(result))
