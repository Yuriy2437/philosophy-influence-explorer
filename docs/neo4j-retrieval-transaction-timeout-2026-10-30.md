# Neo4j retrieval transaction timeout

## Scope

The application now configures a transaction timeout for exactly two
retrieval queries:

- PassageRetriever.search()
- GraphContextRetriever.expand()

Setting:

- NEO4J_RETRIEVAL_TRANSACTION_TIMEOUT_SECONDS
- Initial application default: 10.0 seconds.
- Accepted values: positive, finite numbers.

The default is an initial project choice, not a measured production
latency target.

## Implementation

Neo4jClient.retrieval_query(text) constructs a neo4j.Query object with
the configured timeout.

The two retrievers pass that object to their existing session.run calls.

Cypher text, bound parameters, result consumption, and exception
handling are unchanged.

This step does not change concept-family queries, graph summary,
ingestion, indexing, or seed operations.

## Local compatibility check

Installed driver: neo4j 5.28.5.

Constructing Query("RETURN 1", timeout=7.0) succeeded locally.

Observed fields:

- text: RETURN 1
- timeout: 7.0

This check did not connect to Neo4j.

## Automated validation

Validation date: 2026-10-30.

Targeted command:

```text
uv run --no-sync python -m pytest tests/test_neo4j_client_configuration.py tests/test_passage_retriever.py tests/test_graph_context_retriever.py -q
```

Result: 34 passed in 1.90 seconds; exit code 0.

Full-suite command:

```text
uv run --no-sync python -m pytest -q
```

Result: 291 passed, 1 warning in 18.52 seconds; exit code 0.

git diff --check before documentation: exit code 0.

The full-suite warning concerns the deprecated anyio.abc.BlockingPortal
alias referenced by Starlette TestClient.

## Test coverage

Configuration tests check:

- The default value.
- Rejection of zero, negative values, positive infinity, negative
  infinity, and NaN.
- Loading a value from the environment.
- Query construction by Neo4jClient with a non-default timeout.
- Preservation of query text without opening a session.

Retriever fake sessions require a Query object with the test timeout.
Existing assertions continue to check Cypher text and bound parameters.

## Limitations

No live Aura query or elapsed-time timeout test was performed.

Tests validate configuration and propagation, not actual server-side
termination timing.

Each of the two queries receives its own transaction timeout.

This change does not establish an end-to-end retrieval, HTTP, or
answer-generation deadline. Embedding, connection acquisition,
network operations, and other processing are not collectively bounded
by this setting.

Production behavior and suitability of the initial default require
separate verification.

No production environment variables were changed as part of the
reported local implementation and validation.
