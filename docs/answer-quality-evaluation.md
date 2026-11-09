# Fixed-evidence answer quality evaluation

## Status

Draft AI-assisted rubric pending explicit approval by the project author.

This is a small regression suite based on known local corpus passages.
It is not an independent benchmark or scholarly certification.

## Files

- data/evaluation/answer-quality-v1.json
- src/philosophy_influence_explorer/evaluation/answer_dataset.py
- tests/test_answer_evaluation_dataset.py
- src/philosophy_influence_explorer/evaluation/answer_evidence.py
- tests/test_answer_evaluation_evidence.py
- src/philosophy_influence_explorer/evaluation/answer_runner.py
- tests/test_answer_evaluation_runner.py
- src/philosophy_influence_explorer/evaluation/answer_report.py
- tests/test_answer_evaluation_report.py
- src/philosophy_influence_explorer/evaluation/answer_cli.py
- tests/test_answer_evaluation_cli.py
- docs/answer-quality-evaluation-runs.md

Existing semantic-search datasets and historical judgments are unchanged.

## Scope

Eight cases reuse exact question text from semantic-search-v1.

Each case specifies:

- Fixed evidence passage IDs from the curated local corpus.
- Allowed answer statuses.
- Required semantic points and limitations.
- Prohibited unsupported inferences.
- A rationale for manual review.

The suite includes:

- A contrast between stating a principle and justifying it.
- Direct questions supported by short excerpts.
- Cross-language answering.
- Nonempty but insufficient or irrelevant evidence.

Case selection and evidence are controlled manually.
This is not a replay of semantic search or graph expansion.

## Loader validation

The loader checks:

- Schema, suite identity, and fixed-evidence mode.
- Nonblank fields and duplicate entries.
- Unique answer case IDs and source case IDs.
- Source case existence and exact question text.
- Evidence passage existence in the validated local corpus.

No database, embedding API, or generation API is called.

## Commands

```powershell
uv run pytest -q tests/test_answer_evaluation_dataset.py
uv run ruff check src/philosophy_influence_explorer/evaluation/answer_dataset.py tests/test_answer_evaluation_dataset.py
```

## Interpretation

Passing dataset tests establishes structural and referential consistency.
It does not establish that the rubric is scientifically correct
or that generated answers satisfy it.

Allowed status membership alone is not a quality verdict.
Required points are semantic criteria, not keyword-match requirements.

For insufficient evidence, the limitation concerns supplied passages,
not the absence of relevant knowledge or sources elsewhere.

Candidate review statuses remain candidate.
Generated explanations are not published translations.

## Manual review conventions

Review each answer against the supplied evidence, not against an
unrestricted expectation of what the model may know about the topic.

Required points and limitations are semantic criteria.
Equivalent wording is acceptable; exact phrase matching is not required.

An answered status may include limitations that accurately define
the scope of an otherwise complete answer to the question.

For answer-q1, review requirements depend on the returned status:

- partial must accurately state the humanity-as-end principle,
  preserve never merely as a means, and identify the missing justification.
- insufficient_evidence must explain the missing justification
  without claims, as required by the answer contract.

For answer-negative-n1, related statements about the practical
imperative or autonomy do not count as a partial answer to the
requested hypothetical-versus-categorical comparison.

The q1 and paraphrase-p1 source labels do not imply equivalent
answerability: one question asks why, while the other asks how to act.

Preserve source review metadata. Approval of this rubric does not
promote candidate passages to reviewed status or independently
verify quotations, editions, or translations.

## Fixed evidence construction

build_fixed_evidence selects local corpus passages in the exact order
specified by evidence_passage_ids.

It preserves the text and all provenance fields supported by
GraphContextPassage, including text kind and review status.
It does not promote candidate records to reviewed status.

The function rejects:

- Empty selections.
- Blank or untrimmed selected IDs.
- Duplicate selected IDs.
- Unknown selected IDs.
- Duplicate passage IDs in the supplied corpus collection.

The resulting EvidencePacket contains manually selected passages.
Both semantic_passage_ids and additional_graph_passage_ids are empty:
no semantic retrieval or graph expansion took place.

This intentionally differs from production retrieval packets.
The generator receives the passages but no claimed retrieval membership.

Fields present only in PassageRecord, such as license_status and
position_label, are not included in GraphContextPassage.
The packet is not a complete bibliographic or licensing snapshot.

The function does not call external services or modify input records.
Tests build packets for all eight repository evaluation cases.

## Provider-independent evaluation runner

run_answer_evaluation accepts an AnswerSuite, local corpus passages,
and an AnswerGenerator. It returns a JSON-compatible diagnostic report
without configuring a provider or writing files.

The runner revalidates the suite and prepares every fixed-evidence
packet before calling the generator. Invalid suite or evidence data
aborts the run before any generator call.

Each case receives one generator call, without runner-level retries.
Ordinary generation and answer-validation exceptions are recorded
per case; later cases continue. KeyboardInterrupt is not swallowed.

Each result includes:

- A snapshot of the complete case, including its review criteria.
- The supplied evidence packet and its SHA-256 hash.
- Generator-call duration in seconds.
- A draft answer when the returned GroundedAnswer can be serialized.
- An answer that passed structure and reference-membership checks.
- Separate structure, reference-membership, and allowed-status checks.
- Error stage, exception type, and message when applicable.
- Empty manual-review verdict and notes.

A null check means the check was not performed.
A disallowed answer status is recorded as status_allowed=false,
not as an execution error. The structurally valid answer is retained
if its references belong to the supplied evidence.

The runner revalidates serialized GroundedAnswer output rather than
trusting an existing model instance. Reference validation establishes
passage-ID membership only, not entailment or scholarly correctness.

The evidence hash covers the complete ordered packet using UTF-8 JSON
with ensure_ascii=false, sort_keys=true, separators=(',', ':'),
and allow_nan=false. It identifies the evidence snapshot, not the
complete experiment.

Tests use a substituted generator and local corpus data.
No live provider call or automatic semantic grading is performed.

The runner does not implement timeouts, report-file persistence,
a CLI, or live-provider configuration. A supplied generator may itself
use external services or implement internal retries.

## JSON report persistence

save_answer_report saves a supplied report to a new UTF-8 JSON file.
It is separate from the runner and does not execute generation,
validate the report schema, or assign manual-review verdicts.

The output uses readable indentation, unescaped Unicode, no UTF-8 BOM,
and a final LF newline. Non-finite numbers are rejected.

Serialization completes before the destination is opened.
A serialization failure does not create a destination file.
The destination is opened in exclusive creation mode: existing files,
including empty files, are never overwritten.

Parent directories must already exist.
Filesystem errors propagate to the caller.
Writing is not atomic: an I/O failure after file creation may leave
an incomplete report.

Tests save and reload a complete runner report produced with a
substituted generator and local corpus data. They cover recorded
generation errors, successful structured answers, evidence snapshots,
hash preservation, empty manual-review fields, Unicode, overwrite
protection, serialization failures, and missing parent directories.

JSON arrays represent both Python lists and tuples.
The round-trip comparison uses the JSON-normalized report.

## Explicitly gated Gemini evaluation command

The answer_cli module runs one explicitly selected evaluation case
through the existing GeminiAnswerGenerator and saves a JSON report.

The command requires:

- An explicit case ID.
- An explicit bare model ID, without a Production-default fallback.
- An output path whose parent directory already exists.
- The --allow-network flag.
- GOOGLE_API_KEY in the process environment.

The command does not automatically load .env or instantiate application
Settings. It does not use retrieval, embeddings, Neo4j, or the API route.
Production generation settings are unchanged.

Before generation, it checks the network gate, destination path,
selected case, local dataset, and generator configuration.
The runner prepares fixed evidence before calling the generator.

The output-path check is not a reservation. Exclusive creation during
saving prevents overwriting a file that appears after the preflight.
A saving failure may occur after a provider request has completed.
Report writing remains non-atomic.

The report includes:

- The requested model ID, not a verified serving-model version.
- UTC start and finish timestamps around the runner execution.
- The selected case ID.
- HTTP timeout and input-byte limit.
- Runner and adapter retry counts, both zero.
- A SHA-256 hash of the UTF-8 system instruction.
- An indication that rejected provider output is not retained.

The API key is not added to report metadata.
Case criteria are retained in the report but are not sent to Gemini.

The existing adapter performs at most one HTTP request per generate call,
without retries. Input validation may reject a call before HTTP.
The configured HTTP timeout is not a total evaluation deadline.

The adapter validates answer structure and reference membership before
returning. Answers rejected there appear as generation-stage errors in
the runner report; their original provider output is not retained.

Exit codes:

- 0: The report was saved and all automatic checks passed.
  Manual semantic review is still pending.
- 1: The report was saved, but a case error or failed automatic check
  was recorded.
- 2: Argument parsing, setup, or report saving failed.

Tests substitute HTTP responses and do not call the live provider.
The --allow-network flag is an explicit local execution gate,
not Production authentication or authorization.

## Observed live runs

Thirteen CLI invocations cover all eight distinct cases. Twelve JSON
reports were saved; one invocation stopped during local setup because
GOOGLE_API_KEY was absent and produced no report or provider request.

Execution outcomes and AI-assisted semantic assessments are recorded in
[the run review log](answer-quality-evaluation-runs.md).

Eight invocations returned answers, all of which passed automatic checks.
AI-assisted review assessed:

- Four answers as meeting the draft criteria without a noted wording caveat.
- Two answers as meeting them with wording caveats.
- Two answers as not meeting them: answer-q5 substituted derived from
  for abstracts from, and answer-paraphrase-p2 omitted a required limitation.

Four invocations ended with HTTP 503 and saved reports without assessable
answers: the initial q1 invocation, the initial paraphrase-p1 invocation,
and the first two negative-n1 invocations. Automatic checks were not
performed for these failures.

Separate manual retries returned assessable answers for q1 and
paraphrase-p1, completing one observed why-versus-how contrast.

After the two negative-n1 HTTP 503 failures, a further invocation stopped
locally because the API key was absent. Once the process environment was
configured, another separate invocation returned insufficient_evidence,
with no claims and an explicit explanation that the supplied passages
do not provide the requested comparison. This answer meets the current
draft case criteria according to AI-assisted review.

Each of the eight cases now has one returned answer and an AI-assisted
semantic assessment. This completes case coverage for the recorded
fixed-evidence series, not repeated-sample testing or end-to-end
answer-workflow evaluation.

These observations are not a statistical estimate of reliability,
independent scholarly review, or project-author semantic approval.
Original JSON reports remain unchanged, with manual_review fields null.

## Not implemented in this increment

- A workflow for entering and validating completed manual reviews.
- Atomic report-file publication.
- Project-author semantic approval of the observed answers.
- End-to-end answer-workflow evaluation.
- Corpus snapshot comparison with Aura.
- Model-based judging.

Production generation settings are not changed by these files.
