# Embedding timeout validation

## Scope

Embedding timeouts must be positive and finite.

Validation is enforced in:

- Settings.embedding_timeout_seconds.
- GeminiEmbeddingProvider.__init__().
- OllamaEmbeddingProvider.__init__().

The EMBEDDING_TIMEOUT_SECONDS default remains 60.0 seconds.

HTTP request construction, provider selection, retries, response
validation, and error handling are unchanged.

The generation provider is not changed in this step.

## Automated validation

Validation date: 2026-10-31.

Targeted command:

```text
uv run --no-sync python -m pytest tests/test_embedding_timeout_configuration.py tests/test_embeddings.py tests/test_gemini_embeddings.py tests/test_ollama_embeddings.py -q
```

Result: 43 passed in 0.79 seconds; exit code 0.

Full-suite command:

```text
uv run --no-sync python -m pytest -q
```

Result: 310 passed, 1 warning in 8.93 seconds; exit code 0.

These results were obtained before final formatting-only cleanup
and addition of this document.

The warning concerns the deprecated anyio.abc.BlockingPortal alias
referenced by Starlette TestClient.

## New test coverage

The new test module contains 19 collected cases:

- Default timeout: 1 case.
- Invalid Settings values: 5 cases.
- Environment loading: 1 case.
- Invalid direct-constructor values across two providers: 10 cases.
- Settings-to-factory-to-HTTP timeout propagation: 2 cases.

Rejected values are zero, a negative number, positive infinity,
negative infinity, and NaN.

Propagation tests use a non-default timeout of 8.5 seconds.
HTTP calls are replaced with test doubles.

Existing provider tests also check timeout forwarding and handling
of simulated ReadTimeout errors.

## Limitations

This change validates timeout configuration. It does not add an
end-to-end HTTP, embedding-batch, retrieval, or workflow deadline.

No real provider request or elapsed-time timeout test was performed
for this validation.

No production environment variables were changed as part of the
reported local implementation and validation.
