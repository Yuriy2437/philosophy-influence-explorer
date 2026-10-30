# Neo4j connection timeout configuration

## Scope

The application now explicitly passes two connection-related timeout
settings to GraphDatabase.driver:

- NEO4J_CONNECTION_TIMEOUT_SECONDS: default 10 seconds.
- NEO4J_CONNECTION_ACQUISITION_TIMEOUT_SECONDS: default 20 seconds.

Both settings must be positive and finite.

These are initial application defaults, not an end-to-end workflow
deadline or a guarantee that retrieval completes within a fixed time.

The settings affect Neo4jClient instances across the application,
not only the answer-generation route.

## Implementation

Settings are loaded through the existing application Settings class.

Neo4jClient passes them as:

- connection_timeout
- connection_acquisition_timeout

No Cypher query text, transaction timeout, retry policy, HTTP timeout,
or route contract is changed in this step.

## Validation environment

Versions reported from the local project environment:

- neo4j: 5.28.5
- httpx: 0.28.1

## Automated validation

Validation date: 2026-10-30.

Targeted command:

```text
uv run --no-sync python -m pytest tests/test_neo4j_client_configuration.py tests/test_database_health.py tests/test_database_disabled.py -q
```

Result: 17 passed, 1 warning in 3.53 seconds; exit code 0.

Full-suite command:

```text
uv run --no-sync python -m pytest -q
```

Result: 283 passed, 1 warning in 6.96 seconds; exit code 0.

git diff --check: exit code 0.

The warning concerns the deprecated anyio.abc.BlockingPortal alias
referenced by Starlette TestClient.

## Test coverage

The new configuration tests check:

- Default values.
- Rejection of zero, negative, infinite, and NaN values.
- Loading values from environment variables.
- Passing configured values to a mocked driver factory.
- Closing the underlying driver.
- Construction and closure using the real installed driver while
  DNS resolution and socket connection functions are blocked.

The real-driver test does not call verify_connectivity or execute a query.
It confirms configuration acceptance without a database connection.

## Limitations

No live Aura connection or elapsed-time timeout test was performed.

These settings do not establish:

- A Cypher execution-time limit.
- A complete bound on all network operations.
- An HTTP response deadline.
- A total answer-workflow duration.

The deployment previously checked keeps generation unavailable.
This change does not authorize enabling generation or changing
production environment variables.

Deployment of this change and behavior under production connection
failures require separate verification.
