# LangGraph acceptance — 2026-11-03

## Scope and version

Verified application commit: 87d8b59.

This acceptance covers the existing retrieval and answer workflows,
operator access, evidence handling, and cooperative execution budget.
It does not approve public answer generation.

## Implementation review

Reviewed:
- Compiled retrieval workflow and nested answer workflow.
- Request normalization and validation.
- Evidence deduplication and provenance-conflict rejection.
- Structured answer validation and evidence-reference membership.
- Execution-budget propagation and stage-boundary checks.

Targeted workflow, evidence, and contract tests:
65 passed in 3.26s.

Access and answer API tests:
43 passed, 1 dependency deprecation warning in 3.86s.

These are two targeted test runs, not a new full-suite run.

## Live retrieval

Production database health returned:
- status: ok
- database: ed77f4a1

Passage search:
- Query: being, nothing, and becoming
- Limit: 3
- Returned 3 passages: EN editorial, DE primary quote, RU editorial.

Retrieval-only query:
- Semantic limit: 3
- Graph limit: 5
- Returned 3 semantic passages and 5 graph paths.
- Returned paths had consistent seeds and edge endpoints.
- Related passages were already present in semantic results.

The /query route calls the retrieval service directly.
It does not execute LangGraph or prepare EvidencePacket.

The documented live retrieval-workflow check from 2026-10-28
remains historical evidence:
1 semantic passage, 2 graph paths, 3 unique evidence passages,
including 2 additional graph passages; result PASS.

A new standalone local live retrieval-workflow check did not complete.
Local settings targeted localhost Neo4j and Ollama, not Aura.
Persistent local settings were not changed.

## Operator access

With generation enabled and a server token configured:
- Production request without a token returned 401:
  Generation access denied.

Tests verify rejected requests do not create answer services.

## Live answer workflow

Production deployment was confirmed Ready at commit 87d8b59.

Configured:
- generation_model: gemini-3.5-flash-lite
- generation_timeout_seconds: 60
- answer_workflow_timeout_seconds: 120

One authorized request was executed without automatic retries:
- Query: How is becoming related to being and nothing?
- limit: 1
- graph_limit: 5
- is_verbatim: true
- is_editorial: false

Result:
- HTTP 200
- Client-observed elapsed time: 5.52 seconds
- Content-Type: application/json; charset=utf-8
- Cache-Control: no-store
- mode: evidence_grounded_answer
- answer.status: answered
- 2 claims referencing passage:hegel:wl:being:de
- 1 evidence passage: primary_quote, reviewed, verbatim, non-editorial
- No additional graph passage IDs.

The answer was broadly consistent with the supplied excerpt.
The phrase "derived from being and nothing" was less precise than
"abstracting from being and nothing".
This was not an expert translation or scholarly-accuracy evaluation.

## Negative scenarios

Reviewed passing tests cover:
- Disabled generation and missing or invalid operator access.
- Invalid request bodies before service creation.
- Retrieval failure preventing generation.
- Generation failures and sanitized HTTP errors.
- Invalid answer structure and unknown passage references.
- Cooperative budget expiry and sanitized HTTP 504.
- A fresh execution budget for each request.

No deliberate live database outage or live timeout was induced.

## Final operational state

GENERATION_ENABLED=false was redeployed.

The permanent production domain then returned HTTP 503:
Answer generation is unavailable.

Retained current deployment:
dpl_FrTgG4sa7216SzzTNTJnqLvKQ2sP

User confirmed deletion of intermediate deployments:
- dpl_AdnWagkSjzmeu7ssVJNEdEkxo6Ns
- dpl_9TZREcXnzwu2HrS4yeYfWJpkTWZL

The earliest listed deployment was retained:
dpl_4Xm2JiNrTZ5XoqLfkL8oTqNdDrX9

Before deletion, unauthenticated requests to all four unique
deployment URLs were blocked by Vercel Authentication.
Those platform responses did not establish application gate settings.

## Limitations

- The live answer check covers one question and one filter configuration.
- Reference membership does not establish semantic entailment,
  quotation accuracy, completeness, or independent corroboration.
- The cooperative budget cannot interrupt an already running
  synchronous external call.
- The live answer response does not expose graph-path counts.
- An explicit blank evidence-passage-ID test was noted as optional follow-up.
- Public generation remains disabled.
- No secrets are included in this report.
