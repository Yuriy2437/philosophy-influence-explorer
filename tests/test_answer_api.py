"""Test the answer endpoint without external services."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import philosophy_influence_explorer.main as application
from philosophy_influence_explorer.api.routes import answers
from philosophy_influence_explorer.config import Settings, get_settings
from philosophy_influence_explorer.generation.contracts import GroundedAnswer
from philosophy_influence_explorer.generation.gemini import (
    GeminiAnswerGeneratorError,
)
from philosophy_influence_explorer.retrieval.semantic_graph_retriever import (
    SemanticGraphResult,
)


@pytest.fixture
def setup_api(monkeypatch):
    settings = Settings(
        _env_file=None,
        neo4j_enabled=False,
        generation_enabled=True,
        generation_access_token="operator-test-token",
        generation_model="test-model",
        generation_timeout_seconds=5.0,
        google_api_key="google-test-key",
    )

    retriever = Mock()
    retriever.retrieve.return_value = SemanticGraphResult((), ())

    generator = Mock()
    generator.generate.return_value = GroundedAnswer(
        status="insufficient_evidence",
        claims=[],
        limitations=["No suitable evidence was supplied."],
    )

    retriever_factory = Mock(return_value=retriever)
    generator_factory = Mock(return_value=generator)

    monkeypatch.setattr(application, "get_settings", lambda: settings)
    monkeypatch.setattr(
        answers,
        "get_semantic_graph_retriever",
        retriever_factory,
    )
    monkeypatch.setattr(
        answers,
        "GeminiAnswerGenerator",
        generator_factory,
    )

    app = application.create_app()
    app.dependency_overrides[get_settings] = lambda: settings

    return (
        app,
        settings,
        retriever,
        generator,
        retriever_factory,
        generator_factory,
    )


def authorization() -> dict[str, str]:
    return {"Authorization": "Bearer operator-test-token"}


def test_answer_runs_workflow_once(setup_api) -> None:
    app, _, retriever, generator, retrieval_factory, generation_factory = setup_api

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            headers=authorization(),
            json={"q": "  Explain the distinction.  "},
        )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "query": "Explain the distinction.",
        "mode": "evidence_grounded_answer",
        "answer": {
            "status": "insufficient_evidence",
            "claims": [],
            "limitations": ["No suitable evidence was supplied."],
        },
        "evidence": {
            "passages": [],
            "semantic_passage_ids": [],
            "additional_graph_passage_ids": [],
        },
    }

    retrieval_factory.assert_called_once()
    generation_factory.assert_called_once_with(
        api_key="google-test-key",
        model="test-model",
        timeout_seconds=5.0,
    )
    retriever.retrieve.assert_called_once()
    generator.generate.assert_called_once()

    call = retriever.retrieve.call_args
    assert call.args == ("Explain the distinction.",)
    assert call.kwargs["limit"] == 3
    assert call.kwargs["graph_limit"] == 20
    assert call.kwargs["filters"].is_verbatim is True
    assert call.kwargs["filters"].is_editorial is False


@pytest.mark.parametrize("disabled", [True, False])
def test_denied_request_creates_no_services(setup_api, disabled: bool) -> None:
    app, settings, retriever, generator, retrieval_factory, generation_factory = setup_api
    settings.generation_enabled = not disabled

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            json={"q": "Question"},
        )

    assert response.status_code == (503 if disabled else 401)
    retrieval_factory.assert_not_called()
    generation_factory.assert_not_called()
    retriever.retrieve.assert_not_called()
    generator.generate.assert_not_called()


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"q": "   "},
        {"q": "x" * 501},
        {"q": "Question", "limit": 6},
        {"q": "Question", "model": "client-model"},
    ],
)
def test_invalid_body_creates_no_services(setup_api, body: dict) -> None:
    app, _, retriever, generator, retrieval_factory, generation_factory = setup_api

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            headers=authorization(),
            json=body,
        )

    assert response.status_code == 422
    retrieval_factory.assert_not_called()
    generation_factory.assert_not_called()
    retriever.retrieve.assert_not_called()
    generator.generate.assert_not_called()


def test_missing_google_key_creates_no_services(setup_api) -> None:
    app, settings, _, _, retrieval_factory, generation_factory = setup_api
    settings.google_api_key = None

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            headers=authorization(),
            json={"q": "Question"},
        )

    assert response.status_code == 503
    retrieval_factory.assert_not_called()
    generation_factory.assert_not_called()


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (GeminiAnswerGeneratorError("private-generation-marker"), 502),
        (ValueError("private-validation-marker"), 502),
        (RuntimeError("private-service-marker"), 503),
    ],
)
def test_generation_errors_are_not_successful_answers(
    setup_api,
    error: Exception,
    expected_status: int,
) -> None:
    app, _, _, generator, _, _ = setup_api
    generator.generate.side_effect = error

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            headers=authorization(),
            json={"q": "Question"},
        )

    assert response.status_code == expected_status
    assert "private-" not in response.text
    assert "answer" not in response.json()
    generator.generate.assert_called_once()


def test_retrieval_failure_prevents_generation(setup_api) -> None:
    app, _, retriever, generator, _, _ = setup_api
    retriever.retrieve.side_effect = RuntimeError("private-retrieval-marker")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            headers=authorization(),
            json={"q": "Question"},
        )

    assert response.status_code == 503
    assert "private-retrieval-marker" not in response.text
    generator.generate.assert_not_called()


def test_answer_get_is_not_supported(setup_api) -> None:
    app, _, _, _, retrieval_factory, generation_factory = setup_api

    with TestClient(app) as client:
        response = client.get("/api/v1/answers")

    assert response.status_code == 405
    retrieval_factory.assert_not_called()
    generation_factory.assert_not_called()


@pytest.mark.parametrize("answer_status", ["partial", "insufficient_evidence"])
def test_answer_preserves_nonempty_candidate_evidence(
    setup_api,
    answer_status: str,
) -> None:
    from philosophy_influence_explorer.generation.contracts import AnswerClaim
    from philosophy_influence_explorer.retrieval.passage_retriever import (
        RetrievedPassage,
    )

    app, _, retriever, generator, _, _ = setup_api

    passage = RetrievedPassage(
        id="passage:api-candidate",
        text="Synthetic primary-text fixture, not a real quotation.",
        score=0.8,
        source_id="source:api-test",
        work_id="work:api-test",
        citation_label="Synthetic API fixture",
        language="en",
        text_kind="primary_quote",
        review_status="candidate",
        is_verbatim=True,
        is_editorial=False,
        is_machine_generated=False,
        concepts=(),
    )
    retriever.retrieve.return_value = SemanticGraphResult((passage,), ())

    claims = (
        [
            AnswerClaim(
                text="The supplied fixture contains a statement.",
                passage_ids=[passage.id],
            )
        ]
        if answer_status == "partial"
        else []
    )
    generator.generate.return_value = GroundedAnswer(
        status=answer_status,
        claims=claims,
        limitations=[
            "The supplied text does not explain the requested basis."],
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            headers=authorization(),
            json={"q": "Explain the basis."},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json; charset=utf-8"

    payload = response.json()
    assert payload["answer"]["status"] == answer_status
    assert payload["evidence"]["semantic_passage_ids"] == [passage.id]
    assert payload["evidence"]["additional_graph_passage_ids"] == []
    assert payload["evidence"]["passages"] == [
        {
            "id": passage.id,
            "text": passage.text,
            "source_id": passage.source_id,
            "work_id": passage.work_id,
            "citation_label": passage.citation_label,
            "language": passage.language,
            "text_kind": passage.text_kind,
            "review_status": "candidate",
            "is_verbatim": True,
            "is_editorial": False,
            "is_machine_generated": False,
        }
    ]

    sent_packet = generator.generate.call_args.kwargs["evidence"]
    assert sent_packet.passages[0].text == passage.text
    assert sent_packet.passages[0].review_status == "candidate"
    generator.generate.assert_called_once()


@pytest.mark.parametrize(
    ("factory_name", "error"),
    [
        ("generator", ValueError("private-generator-config-marker")),
        ("retriever", RuntimeError("private-retriever-config-marker")),
    ],
)
def test_service_construction_errors_are_sanitized(
    setup_api,
    factory_name: str,
    error: Exception,
) -> None:
    app, _, retriever, generator, retrieval_factory, generation_factory = setup_api

    if factory_name == "generator":
        generation_factory.side_effect = error
    else:
        retrieval_factory.side_effect = error

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            headers=authorization(),
            json={"q": "Question"},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Answer generation service is unavailable."
    }
    assert "private-" not in response.text
    retriever.retrieve.assert_not_called()
    generator.generate.assert_not_called()

    if factory_name == "generator":
        retrieval_factory.assert_not_called()


def test_answer_openapi_documents_security_and_response(setup_api) -> None:
    app, _, _, _, retrieval_factory, generation_factory = setup_api

    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    operation = document["paths"]["/api/v1/answers"]["post"]

    assert "requestBody" in operation
    assert {"401", "422", "502", "503"} <= set(operation["responses"])
    assert {"GenerationOperatorToken": []} in operation["security"]

    scheme = document["components"]["securitySchemes"]["GenerationOperatorToken"]
    assert scheme["type"] == "http"
    assert scheme["scheme"] == "bearer"

    properties = document["components"]["schemas"]["AnswerResponse"]["properties"]
    assert {"query", "mode", "answer", "evidence"} <= set(properties)

    assert "operator-test-token" not in response.text
    assert "google-test-key" not in response.text
    retrieval_factory.assert_not_called()
    generation_factory.assert_not_called()


def test_unknown_reference_is_rejected_at_http_boundary(setup_api) -> None:
    from philosophy_influence_explorer.generation.contracts import AnswerClaim

    app, _, _, generator, _, _ = setup_api
    generator.generate.return_value = GroundedAnswer(
        status="answered",
        claims=[
            AnswerClaim(
                text="Unsupported synthetic assertion.",
                passage_ids=["passage:unknown"],
            )
        ],
        limitations=[],
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/answers",
            headers=authorization(),
            json={"q": "Question"},
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Answer workflow validation failed."
    }
    assert "Unsupported synthetic assertion" not in response.text
    assert "passage:unknown" not in response.text
    generator.generate.assert_called_once()
