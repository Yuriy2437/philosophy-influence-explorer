"""Test Gemini generation with fake HTTP responses only."""

from __future__ import annotations

import json

import httpx
import pytest

from philosophy_influence_explorer.generation.gemini import (
    GeminiAnswerGenerator,
    GeminiAnswerGeneratorError,
)
from philosophy_influence_explorer.retrieval.graph_context_retriever import (
    GraphContextPassage,
)
from philosophy_influence_explorer.workflows.evidence import EvidencePacket


def generator() -> GeminiAnswerGenerator:
    return GeminiAnswerGenerator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5.0,
    )


def response(payload: object, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("POST", "https://example.test/generate"),
    )


def envelope(answer: dict) -> dict:
    return {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(answer)}]},
            }
        ]
    }


def insufficient_answer() -> dict:
    return {
        "status": "insufficient_evidence",
        "claims": [],
        "limitations": ["No evidence supplied."],
    }


def test_request_and_structured_answer(monkeypatch) -> None:
    captured = {}

    def fake_post(url, *, headers, json, timeout):
        captured.update(
            url=url,
            headers=headers,
            body=json,
            timeout=timeout,
        )
        return response(envelope(insufficient_answer()))

    monkeypatch.setattr(httpx, "post", fake_post)

    answer = generator().generate(
        query_text="  Test question?  ",
        evidence=EvidencePacket((), (), ()),
    )

    assert answer.status == "insufficient_evidence"
    assert captured["url"].endswith("models/test-model:generateContent")
    assert captured["headers"] == {"x-goog-api-key": "test-key"}
    assert captured["timeout"] == 5.0
    body = captured["body"]
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert "responseJsonSchema" in body["generationConfig"]
    data = json.loads(body["contents"][0]["parts"][0]["text"])
    assert data["question"] == "Test question?"
    assert data["passages"] == []
    assert body["systemInstruction"]["parts"][0]["text"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        [],
        {"candidates": []},
        {"candidates": [{"finishReason": "MAX_TOKENS"}]},
        {"candidates": [{"finishReason": "STOP", "content": {}}]},
        {
            "candidates": [
                {
                    "finishReason": "STOP",
                    "content": {"parts": [{"text": "not JSON"}]},
                }
            ]
        },
    ],
)
def test_invalid_response_is_rejected(monkeypatch, payload) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: response(payload),
    )

    with pytest.raises(GeminiAnswerGeneratorError):
        generator().generate(
            query_text="Question",
            evidence=EvidencePacket((), (), ()),
        )


def test_unknown_reference_is_rejected(monkeypatch) -> None:
    payload = envelope(
        {
            "status": "answered",
            "claims": [
                {
                    "text": "Unsupported assertion",
                    "passage_ids": ["passage:unknown"],
                }
            ],
            "limitations": [],
        }
    )
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: response(payload),
    )

    with pytest.raises(GeminiAnswerGeneratorError, match="reference validation"):
        generator().generate(
            query_text="Question",
            evidence=EvidencePacket((), (), ()),
        )


def test_http_error_does_not_expose_body(monkeypatch) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: response(
            {"error": {"message": "sensitive-response-marker"}},
            status_code=429,
        ),
    )

    with pytest.raises(GeminiAnswerGeneratorError) as caught:
        generator().generate(
            query_text="Question",
            evidence=EvidencePacket((), (), ()),
        )

    assert "HTTP 429" in str(caught.value)
    assert "sensitive-response-marker" not in str(caught.value)
    assert "test-key" not in str(caught.value)


def test_transport_failure_is_sanitized(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise httpx.ReadTimeout("sensitive-transport-marker")

    monkeypatch.setattr(httpx, "post", fail)

    with pytest.raises(GeminiAnswerGeneratorError, match="Could not reach") as caught:
        generator().generate(
            query_text="Question",
            evidence=EvidencePacket((), (), ()),
        )

    assert "sensitive-transport-marker" not in str(caught.value)


def test_blank_question_does_not_call_api(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Unexpected API call.")

    monkeypatch.setattr(httpx, "post", fail_if_called)

    with pytest.raises(ValueError, match="must not be blank"):
        generator().generate(
            query_text="   ",
            evidence=EvidencePacket((), (), ()),
        )


def test_nonempty_evidence_preserves_provenance(monkeypatch) -> None:
    record = GraphContextPassage(
        id="passage:test",
        text="Synthetic editorial explanation.",
        source_id="source:test",
        work_id="work:test",
        citation_label="Synthetic fixture",
        language="en",
        text_kind="editorial_summary",
        review_status="curated",
        is_verbatim=False,
        is_editorial=True,
        is_machine_generated=False,
    )
    evidence = EvidencePacket(
        passages=(record,),
        semantic_passage_ids=(),
        additional_graph_passage_ids=(record.id,),
    )
    captured = {}

    def fake_post(url, *, headers, json, timeout):
        captured["body"] = json
        return response(
            envelope(
                {
                    "status": "partial",
                    "claims": [
                        {
                            "text": "Synthetic assertion.",
                            "passage_ids": ["passage:test"],
                        }
                    ],
                    "limitations": ["Only an editorial explanation is supplied."],
                }
            )
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    answer = generator().generate(
        query_text="Question",
        evidence=evidence,
    )

    data = json.loads(captured["body"]["contents"][0]["parts"][0]["text"])
    sent = data["passages"][0]
    assert sent["id"] == record.id
    assert sent["text"] == record.text
    assert sent["source_id"] == record.source_id
    assert sent["work_id"] == record.work_id
    assert sent["citation_label"] == record.citation_label
    assert sent["text_kind"] == "editorial_summary"
    assert sent["review_status"] == "curated"
    assert sent["is_verbatim"] is False
    assert sent["is_editorial"] is True
    assert data["semantic_passage_ids"] == []
    assert data["additional_graph_passage_ids"] == ["passage:test"]
    assert "score" not in sent
    assert answer.claims[0].passage_ids == ["passage:test"]


def test_invalid_outer_json_is_rejected(monkeypatch) -> None:
    invalid_response = httpx.Response(
        200,
        content=b"not JSON",
        request=httpx.Request("POST", "https://example.test/generate"),
    )
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: invalid_response,
    )

    with pytest.raises(
        GeminiAnswerGeneratorError,
        match="invalid response JSON",
    ):
        generator().generate(
            query_text="Question",
            evidence=EvidencePacket((), (), ()),
        )


def test_thought_text_is_not_parsed_as_answer(monkeypatch) -> None:
    payload = {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {"thought": True, "text": "Not the JSON answer."},
                        {"text": json.dumps(insufficient_answer())},
                    ]
                },
            }
        ]
    }
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: response(payload),
    )

    answer = generator().generate(
        query_text="Question",
        evidence=EvidencePacket((), (), ()),
    )

    assert answer.status == "insufficient_evidence"


def test_invalid_answer_structure_is_rejected(monkeypatch) -> None:
    payload = envelope(
        {
            "status": "answered",
            "claims": [],
            "limitations": [],
        }
    )
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: response(payload),
    )

    with pytest.raises(
        GeminiAnswerGeneratorError,
        match="structure or reference validation",
    ):
        generator().generate(
            query_text="Question",
            evidence=EvidencePacket((), (), ()),
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"api_key": "   "},
        {"model": "models/test-model"},
        {"model": "../test-model"},
        {"timeout_seconds": 0},
        {"timeout_seconds": float("inf")},
    ],
)
def test_invalid_generator_configuration_is_rejected(overrides) -> None:
    parameters = {
        "api_key": "test-key",
        "model": "test-model",
        "timeout_seconds": 5.0,
    }
    parameters.update(overrides)

    with pytest.raises(ValueError):
        GeminiAnswerGenerator(**parameters)


@pytest.mark.parametrize("failure_kind", ["http_429", "timeout"])
def test_failed_generation_makes_exactly_one_http_request(
    monkeypatch,
    failure_kind: str,
) -> None:
    call_count = 0

    def fake_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        if failure_kind == "timeout":
            raise httpx.ReadTimeout("Synthetic timeout")

        return response(
            {"error": {"message": "Synthetic rate limit"}},
            status_code=429,
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(GeminiAnswerGeneratorError):
        generator().generate(
            query_text="Question",
            evidence=EvidencePacket((), (), ()),
        )

    assert call_count == 1


@pytest.mark.parametrize("budget_delta", [0, 1, -1])
def test_generation_input_byte_budget_boundary(
    monkeypatch,
    budget_delta: int,
) -> None:
    query = "Почему? Warum? 哲学"
    request_data = {
        "question": query,
        "passages": [],
        "semantic_passage_ids": [],
        "additional_graph_passage_ids": [],
    }
    serialized = json.dumps(request_data, ensure_ascii=False)
    exact_size = len(serialized.encode("utf-8"))
    calls = []

    def fake_post(*args, **kwargs):
        calls.append(kwargs)
        return response(envelope(insufficient_answer()))

    monkeypatch.setattr(httpx, "post", fake_post)

    instance = GeminiAnswerGenerator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5.0,
        max_input_bytes=exact_size + budget_delta,
    )

    if budget_delta < 0:
        with pytest.raises(
            GeminiAnswerGeneratorError,
            match="byte budget",
        ):
            instance.generate(
                query_text=query,
                evidence=EvidencePacket((), (), ()),
            )
        assert calls == []
    else:
        answer = instance.generate(
            query_text=query,
            evidence=EvidencePacket((), (), ()),
        )
        assert answer.status == "insufficient_evidence"
        assert len(calls) == 1
        sent = calls[0]["json"]["contents"][0]["parts"][0]["text"]
        assert sent == serialized


@pytest.mark.parametrize("budget", [0, -1, True, 1.5, "64000"])
def test_invalid_generation_input_budget_is_rejected(budget) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        GeminiAnswerGenerator(
            api_key="test-key",
            model="test-model",
            max_input_bytes=budget,
        )


@pytest.mark.parametrize("oversized_field", ["text", "citation_label"])
def test_default_input_budget_rejects_oversized_evidence_before_http(
    monkeypatch,
    oversized_field: str,
) -> None:
    from dataclasses import replace
    from unittest.mock import Mock

    record = GraphContextPassage(
        id="passage:budget-test",
        text="Synthetic evidence.",
        source_id="source:budget-test",
        work_id="work:budget-test",
        citation_label="Synthetic fixture",
        language="ru",
        text_kind="editorial_summary",
        review_status="candidate",
        is_verbatim=False,
        is_editorial=True,
        is_machine_generated=False,
    )

    oversized_value = "private-evidence-marker:" + ("Ж" * 32_001)
    record = replace(record, **{oversized_field: oversized_value})

    evidence = EvidencePacket(
        passages=(record,),
        semantic_passage_ids=(record.id,),
        additional_graph_passage_ids=(),
    )

    post = Mock(side_effect=AssertionError("Unexpected HTTP request."))
    monkeypatch.setattr(httpx, "post", post)

    instance = GeminiAnswerGenerator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5.0,
    )

    with pytest.raises(
        GeminiAnswerGeneratorError,
        match="byte budget",
    ) as caught:
        instance.generate(
            query_text="Question",
            evidence=evidence,
        )

    post.assert_not_called()
    assert "private-evidence-marker" not in str(caught.value)
    assert "test-key" not in str(caught.value)
    assert record.review_status == "candidate"
    assert getattr(record, oversized_field) == oversized_value
