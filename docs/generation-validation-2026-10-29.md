# Structured generation validation

## Scope

This record covers the provider-independent answer contract, the Gemini
generation adapter, and the retrieval-to-answer workflow.

The workflow prepares evidence, generates a draft answer, and validates
answer structure and passage-reference membership before accepting it.

The Gemini adapter makes one HTTP request per generate call, with no
automatic retries. It requests JSON output and validates the returned
answer locally.

This record does not establish deployment of an answer API or browser UI.

## Automated validation

Validation completed on 2026-10-29.

Targeted command:

```text
uv run --no-sync python -m pytest tests/test_generation_contracts.py tests/test_gemini_generation.py tests/test_answer_workflow.py -q
```

Result: 57 passed in 3.64 seconds; exit code 0.

Full-suite command:

```text
uv run --no-sync python -m pytest -q
```

Result: 201 passed, 1 warning in 11.94 seconds; exit code 0.

Warning: Starlette TestClient references the deprecated
anyio.abc.BlockingPortal alias. This warning did not fail the test run.

The automated tests use synthetic evidence and mocked dependencies.
They do not establish the factual quality of live model responses.

Additional regression coverage includes:

- One HTTP request on HTTP 429 and transport timeout.
- Strict claim and answer field types.
- Rejection of extra claim fields.
- An insufficient-evidence answer with nonempty evidence.
- An accepted answer referencing an additional graph-context passage.

The graph-context workflow test mocks retrieval and generation. It checks
evidence preparation, provenance membership, and reference acceptance,
not live database traversal or model reasoning.

## Live checks

Two live answer-workflow checks were run on 2026-10-28.

Configuration:

- Account tier reported by the operator: Free tier.
- Generation model: gemini-3.5-flash-lite.
- Embedding provider: Gemini.
- Embedding model: gemini-embedding-001.
- Embedding dimensions: 768.
- Semantic limit: 3.
- Graph limit: 20.
- Passage filters: is_verbatim=True, is_editorial=False.

### Q1: Principle versus justification

Question:

Why should a person be treated as an end rather than merely as a means?

Observed result:

- Status: partial.
- Semantic passages: 3.
- Graph paths: 0.
- Unique evidence passages: 3.
- One claim referencing passage:kant:groundwork:2:humanity:en.
- The limitation explicitly states that the supplied passages formulate
  the principle but do not explain why it holds.
- The retrieved Mill passages were not cited as justification of Kant's
  principle.

Report filename:

answer-q1-20261028-142723-426855.json

SHA256:

83B970DEAFDC18A0A5285FF2617CB8ACD60EA7C03DD9EE4AC8CB9FDE866445FD

### N1: Missing distinction

Question:

How does Kant distinguish a hypothetical imperative from a categorical imperative?

Observed result:

- Status: insufficient_evidence.
- Claims: empty.
- Semantic passages: 3.
- Graph paths: 0.
- Unique evidence passages: 3.
- The limitation identifies the absence of the requested distinction
  from the supplied passages.
- The answer does not supply definitions from background knowledge.

Report filename:

answer-n1-20261028-164455-176087.json

SHA256:

AD5270571B0FD6E54E8083C7150CD5D12382935794E8B541012714C0FD17AAF7

## Evidence and review limitations

All passages displayed for the two live checks had review_status=candidate.
Successful generation does not change their review status.

Structure and reference validation do not establish:

- Claim entailment from cited text.
- Quotation or edition accuracy.
- Answer completeness.
- Historical influence.
- Scholarly approval.

The live outputs received a preliminary assistant review against the
displayed evidence. They were not recorded as operator-approved scholarly
annotations. The original reports retain semantic_grounding_reviewed=false.

Both live checks returned zero graph paths. Live generation using nonempty
graph context has therefore not been demonstrated by these checks.

The generator receives passage records and retrieval-membership IDs.
Graph paths and semantic scores remain in the retrieval result; graph
relations are not independently supplied as an influence argument.

The temporary launchers were deleted. This document and the archived
reports are not a complete reproducibility bundle: a versioned runner
and a fixed dataset snapshot would be needed for stronger reproducibility.

## Artifact handling

The two JSON reports are retained outside the repository in the sibling
evaluation-reports directory. Do not edit the original report files.

This document records the hashes reported during validation; it does not
represent a new independent hash verification.

Do not include API keys, database credentials, or credential files in
the commit.
