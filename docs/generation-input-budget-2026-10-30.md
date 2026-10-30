# Generation input byte budget

## Scope

The Gemini answer generator now limits the UTF-8 byte size of its
serialized user input before issuing the generation HTTP request.

Default max_input_bytes: 64,000.

The measured JSON object contains:

- The normalized question.
- Full supplied passage records, including provenance.
- Semantic passage IDs.
- Additional graph passage IDs.

The measured serialized string is also the string sent in the user
content part. Input at the exact limit is accepted. Input exceeding
the limit is rejected without a generation HTTP request.

No passages are silently truncated or removed. Budget rejection raises
GeminiAnswerGeneratorError and is not an insufficient_evidence answer.
The existing answer API maps this exception to HTTP 502.

## Budget boundaries

This is a local input-data policy, not a Gemini provider limit.

The budget does not include the system instruction, response JSON schema,
or outer HTTP request envelope. It is not a token count.

The guard runs after retrieval has prepared evidence. Embedding and
database operations may already have occurred.

The check does not impose a raw incoming request-body limit, a memory
allocation limit, a global quota budget, or an end-to-end deadline.

The constructor parameter is server-controlled. No new client-selectable
HTTP field or environment setting is introduced.

## Automated validation

Validation date: 2026-10-30.

Targeted command:

```text
uv run --no-sync python -m pytest tests/test_gemini_generation.py tests/test_answer_api.py -q
```

Result: 52 passed, 1 warning in 3.99 seconds; exit code 0.

Full-suite command:

```text
uv run --no-sync python -m pytest -q
```

Result: 271 passed, 1 warning in 6.58 seconds; exit code 0.

git diff --check: exit code 0.

Coverage includes exact byte boundaries with multilingual input,
invalid budget values, oversized passage text, oversized citation
metadata, no HTTP call on rejection, and unchanged evidence records.

The warning concerns the deprecated anyio.abc.BlockingPortal alias
referenced by Starlette TestClient.

## Deployment status

These results are local automated checks, not a live generation test.

Generation remains disabled in the deployment previously checked.
This change does not authorize production enablement.

Vercel settings reported by the operator: Hobby, Fluid Compute enabled,
Standard CPU, 1 vCPU, 2 GB memory, Function Max Duration 300 seconds.
These settings do not establish an end-to-end workflow deadline.
