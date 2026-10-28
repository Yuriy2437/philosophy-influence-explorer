# LangGraph retrieval workflow

## Scope

The workflow orchestrates existing semantic retrieval and graph expansion.
It does not generate answers or assess evidence sufficiency.

Execution:

```text
START
  -> validate_request
  -> retrieve_context
  -> prepare_evidence
  -> END
```

## Implementation

- workflows/retrieval_workflow.py defines state, request validation,
  and graph construction.
- workflows/evidence.py prepares unique passage records.
- SemanticGraphRetriever is injected into the graph.
- Graph construction does not create database or embedding clients.
- Existing retrieval services and API routes are unchanged.

## State and evidence

The state preserves the original SemanticGraphResult:

- semantic passages retain their order and similarity scores;
- graph context retains all returned paths and edge metadata.

EvidencePacket contains:

- unique passage records with text and provenance;
- semantic passage IDs;
- additional graph passage IDs.

Unique semantic records appear first, followed by additional
graph records in first-occurrence order.

Additional graph passages are not assigned similarity scores.
Multiple paths do not imply independent corroboration.

Conflicting text or provenance for the same passage ID raises an error.
A graph path whose seed is absent from semantic results is rejected.
Retrieval and evidence-preparation failures are not converted
into successful empty results.

The workflow does not independently revalidate all retrieval
filters or graph-edge rules. Those remain responsibilities
of the existing retrieval services.

## Dependencies

The initial implementation was tested with LangGraph 1.2.18.
The resolved dependency versions are recorded in uv.lock.

## Autonomous tests

```powershell
uv run --no-sync python -m pytest tests/test_retrieval_workflow.py tests/test_workflow_evidence.py -q
```

Confirmed locally:

- Workflow tests: 21 passed.
- Full tests suite: 144 passed, 1 dependency warning.
- Ruff checks for the new workflow files and tests passed.
- git diff --check passed.

These tests use synthetic data and mocked retrieval.
Docker, Ollama, Aura, and Gemini are not required.

## Live verification — 2026-10-28

Executed locally through the compiled graph with Aura and Gemini:

- Model: gemini-embedding-001.
- Dimensions: 768.
- Query: How is becoming related to being and nothing?
- Semantic limit: 1.
- Global graph limit: 20.
- No language, concept-family, or provenance restrictions.

Semantic result:

- passage:hegel:wl:being:en
- Similarity: 0.886, rounded for display.
- editorial_summary, curated.
- Non-verbatim, editorial.

Graph paths:

- passage:hegel:wl:being:en
  -> concept:becoming
  <- passage:hegel:wl:being:de
- passage:hegel:wl:being:en
  -> concept:becoming
  <- passage:hegel:wl:being:ru

Additional evidence:

- DE: primary_quote, reviewed, verbatim, non-editorial.
- RU: editorial_summary, curated, non-verbatim, editorial.

Counts:

- Semantic passages: 1.
- Graph paths: 2.
- Unique evidence passages: 3.
- Additional graph passages: 2.

The verification checked evidence membership and ordering,
graph seed membership, edge directions, edge IDs,
and allowed edge review statuses.

Final result:
PASS: workflow completed; evidence and path checks passed.

Credentials were supplied interactively to a temporary script.
Persistent local settings were not changed.
The temporary script was removed.
No seed, reindexing, or graph writes were performed.
Docker and Ollama were not used.

## Limitations

- The live check covers one question and one filter configuration.
- Three passage records do not establish three independent sources.
- Editorial summaries are not translations.
- Similarity is not a measure of truth or answer sufficiency.
- No answer generation, evidence grading, query rewriting,
  conversation memory, or checkpointing was added.
- No API or published deployment integration was added.
- Scientific accuracy and corpus completeness were not evaluated.
