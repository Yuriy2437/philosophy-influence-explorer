# Cooperative answer execution budget

## Scope

The operator-only answer endpoint now creates one execution budget
per authorized and validated request.

Setting:

- ANSWER_WORKFLOW_TIMEOUT_SECONDS
- Initial application default: 120.0 seconds.
- Accepted values: positive, finite numbers.

The default is an initial project choice, not a measured latency
target or a hard response-time guarantee.

The budget starts in the answer route handler, after access checking
and request-body validation. It includes service construction and
the subsequent workflow and response preparation.

## Implementation

ExecutionBudget uses a monotonic clock and a single deadline.

The same object is passed through:

- Answer workflow state.
- Nested retrieval workflow state.
- SemanticGraphRetriever.retrieve().
- PassageRetriever.search().

Checks occur around:

- Service construction.
- Query embedding.
- Passage query execution and result processing.
- Graph-context expansion.
- Evidence preparation.
- Answer generation.
- Answer structural and reference validation.
- API response construction.

Calls without a budget preserve their previous behavior.

Embedding and generation provider interfaces are unchanged.
Existing HTTP and Neo4j timeout settings are unchanged.
No automatic retries are added.

## HTTP behavior

ExecutionBudgetExceededError is handled before RuntimeError.

Detected budget expiry returns:

- HTTP 504.
- Detail: Answer execution time budget exceeded.
- Cache-Control: no-store.

The 504 response is included in OpenAPI.

Existing access checks and generation configuration are unchanged.

## Automated validation

Validation date: 2026-11-02.

Targeted command:

```text
uv run --no-sync python -m pytest tests/test_answer_budget_configuration.py tests/test_answer_api.py tests/test_answer_workflow.py tests/test_retrieval_workflow.py tests/test_generation_access.py -q
```

Result: 84 passed, 1 warning in 8.63 seconds; exit code 0.

Full-suite command:

```text
uv run --no-sync python -m pytest -q
```

Result: 348 passed, 1 warning in 8.08 seconds; exit code 0.

git diff --check before documentation: exit code 0.

The warning concerns the deprecated anyio.abc.BlockingPortal alias
referenced by Starlette TestClient.

## Added test coverage

The full suite increased from 310 to 348 cases:

- ExecutionBudget: 10 cases.
- Passage retrieval budget boundaries: 3 cases.
- Composed semantic and graph retrieval: 5 cases.
- Retrieval workflow budget handling: 5 cases.
- Answer workflow budget handling: 4 cases.
- Budget configuration: 7 cases.
- Answer API budget handling: 4 cases.

Tests use controlled clocks, mocks, and fake dependencies.
They do not sleep or require live database or provider requests.

The existing OpenAPI test now also checks the 504 response.

## Limitations

This is a cooperative budget, not forced cancellation.

An operation already in progress is not interrupted.
Its result is rejected if a subsequent budget check detects expiry.

Remaining time is not forwarded as a reduced HTTP or Neo4j timeout.
A dependency started just before expiry may continue beyond the budget.

If a dependency raises its own exception before the next budget
check, existing error handling applies; the response is not
necessarily 504.

The budget does not cover time before route-handler execution or
network delivery of the response.

No background executor, cancellation mechanism, distributed deadline,
or workflow checkpoint persistence is introduced.

No live elapsed-time test was performed.
Production behavior requires separate verification.

No Vercel settings or production environment variables were changed
as part of this local implementation and validation.
Generation remains disabled under the previously checked configuration.
