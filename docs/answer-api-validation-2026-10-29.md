# Operator-only answer API validation

## Scope

This change connects the existing answer workflow to:

POST /api/v1/answers

The existing retrieval-only POST /api/v1/query contract is unchanged.
No browser generation interface is added.

Generation is disabled by default. This record does not establish
production deployment, production enablement, or a live HTTP generation
check.

## Server configuration

New settings:

- GENERATION_ENABLED: false by default.
- GENERATION_ACCESS_TOKEN: optional secret; required for access when enabled.
- GENERATION_MODEL: gemini-3.5-flash-lite by default.
- GENERATION_TIMEOUT_SECONDS: 60 seconds by default; positive and finite.

GOOGLE_API_KEY remains the provider key. It is not the operator access token.

Missing or blank operator-token configuration causes generation access
to fail closed with HTTP 503. Missing or invalid client credentials
return HTTP 401 when generation and server-token configuration permit
access checking.

The operator token is supplied using the Authorization: Bearer header.
Do not put real tokens in URLs, browser assets, examples, or the repository.

## Request and response

The request accepts:

- q: 1 to 500 characters; whitespace-only questions are rejected.
- limit: 1 to 5; default 3.
- graph_limit: 1 to 20; default 20.
- Optional bounded language and concept_family filters.
- is_verbatim: true by default.
- is_editorial: false by default.

The request uses strict validation and rejects extra fields.
Clients cannot select the generation model, replace the system
instruction, or supply their own evidence packet.

The response contains:

- Normalized query.
- mode: evidence_grounded_answer.
- Structured answer: status, claims, limitations.
- The full passage evidence packet supplied to the generator.
- Semantic and additional graph passage IDs.

Evidence preserves provenance and review_status. No vector score is
invented for evidence records.

Successful responses include Cache-Control: no-store.

## Execution and errors

Service construction is called inside the route handler, after access
approval and successful request validation.

One accepted HTTP request invokes one answer workflow. No automatic
workflow retries are added by this route.

Error mapping:

- 401: missing or invalid operator access.
- 422: invalid request body.
- 502: generation adapter failure or workflow/output validation failure.
- 503: disabled generation, unavailable configuration, or infrastructure
  failure handled by the route.
- 405: GET is not supported.

An infrastructure or validation failure is not converted into an
insufficient_evidence answer.

The generation adapter currently maps upstream HTTP errors to its generic
generation exception; the route does not preserve upstream status codes.

The application's existing lifespan may initialize its enabled Neo4j
client independently of a particular request. The access gate prevents
request-triggered answer-service construction and workflow execution;
it is not a replacement for application lifecycle configuration.

## Automated validation

Validation date: 2026-10-29.

Targeted command:

```text
uv run --no-sync python -m pytest tests/test_answer_api.py tests/test_generation_access.py tests/test_answer_schemas.py tests/test_query_api.py -q
```

Result: 75 passed, 1 warning in 5.28 seconds; exit code 0.

Full-suite command:

```text
uv run --no-sync python -m pytest -q
```

Result: 261 passed, 1 warning in 6.46 seconds; exit code 0.

git diff --check: exit code 0.

Warning: Starlette TestClient references the deprecated
anyio.abc.BlockingPortal alias. The warning did not fail either run.

Tests cover settings, access denial before answer-service creation,
request validation, one workflow execution, candidate evidence
serialization, insufficient evidence with nonempty passages, unknown
passage-reference rejection, sanitized errors, and OpenAPI security.

HTTP integration tests use the real application and answer workflow with
mocked retrieval and generation services. They do not make live provider
or database requests.

## Limitations and deployment boundary

This is an operator-only integration, not a public generation launch.

A shared operator token is not per-user authorization, a rate limiter,
or a global quota budget.

There is no new global request budget, concurrency limit, raw request-body
size limit, or aggregate evidence-text/token budget in this change.

Count limits do not bound the size of individual passage texts.

The existing public retrieval endpoints are not protected by the new
generation gate and may independently consume embedding quota.

Structure and passage-reference membership do not establish entailment,
quotation accuracy, answer completeness, or scholarly approval.
Candidate evidence remains candidate.

Live generation through the new HTTP endpoint and production-platform
timeout compatibility have not been demonstrated in this stage.

Production enablement requires a separate controlled decision. Keep
generation disabled until deployment configuration and operational
limits have been reviewed.
