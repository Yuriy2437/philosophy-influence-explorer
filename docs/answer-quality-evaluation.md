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

## Not implemented in this increment

- A workflow for entering and validating completed manual reviews.
- Atomic report-file publication.
- Live-provider execution and configuration.
- End-to-end answer-workflow evaluation.
- Corpus snapshot comparison with Aura.
- Model-based judging.

Production generation settings are not changed by these files.
