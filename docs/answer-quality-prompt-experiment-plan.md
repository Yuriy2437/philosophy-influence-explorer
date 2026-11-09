# Fixed-evidence prompt experiment plan

## Status and scope

Draft plan for a controlled system-instruction experiment.

This document does not approve the draft evaluation rubric, authorize
network calls, change the Production instruction, or establish that
the proposed candidate improves answer quality.

The experiment concerns fixed-evidence answer generation only.
It does not evaluate retrieval, graph expansion, or the end-to-end
answer workflow.

## Recorded baseline

Baseline documentation commit:

- 5adf991 — docs: complete fixed-evidence evaluation case coverage.

Baseline system instruction SHA-256:

```text
da9f8bf938a147e993c38a66ff4e829adcc44effa5c0dd1452c901cbba87b4d2
```

Requested model:

- gemini-3.5-flash-lite.

The serving-model version was not captured in the baseline reports.
Matching the requested model ID in a future run does not establish
that the serving-model version is unchanged.

The recorded baseline contains:

- 13 CLI invocations.
- 12 saved JSON reports.
- Eight returned answers covering all eight cases.
- Four HTTP 503 failures.
- One local missing-key failure without a provider request or report.

All eight returned answers passed automatic checks.
AI-assisted semantic review assessed:

- Four answers as meeting the draft criteria without a noted wording caveat.
- Two as meeting them with wording caveats.
- Two as not meeting them: answer-q5 and answer-paraphrase-p2.

Original reports remain unchanged, with manual_review fields null.

## Motivation

Two semantic nonconformities motivate this experiment:

1. answer-q5 replaced a unity that abstracts from being and nothing
   with an abstract unity derived from them.
2. answer-paraphrase-p2 omitted the required clarification that
   identifying a permissible purpose does not establish sufficient
   grounds for a particular coercive measure.

Wording caveats were also recorded for answer-paraphrase-p1
and answer-q6. They remain secondary observations, not newly imposed
failure criteria.

## Hypothesis

An additional general instruction to preserve logical relationships,
scope, and limits of inference may improve semantic fidelity and
coverage of required limitations without degrading supported answers
or appropriate insufficient_evidence responses.

This is a hypothesis, not an established result.

## Candidate instruction

Candidate ID: semantic-fidelity-v1.

The candidate consists of the complete baseline SYSTEM_INSTRUCTION,
unchanged, followed by one blank line and exactly this additional text:

> Preserve the logical relationships and scope expressed in the passages, including negation, contrasts, conditions, and qualifications. Do not replace a relationship with a different one merely because the wording sounds similar. When explaining a rule or principle, distinguish what the passage establishes from what it leaves undecided. If the question requires a conclusion that the passage does not establish, state that limitation explicitly rather than implying that the supported point settles the whole question.

No case IDs, author names, source-specific expressions, or expected
case answers are added to the candidate instruction.

The exact candidate instruction and its SHA-256 must be recorded before
any experiment request. Do not edit the candidate during the run.

## Known-set limitation

The candidate was designed after reviewing results for all eight cases.

Evaluation on these same cases is a known-set regression comparison,
not an independent test of generalization.

Do not describe a better result on this set as evidence of broad
model improvement. Additional unseen cases would require a separate
plan and review.

## Conditions held constant

For both baseline-instruction and candidate-instruction runs:

- Suite: answer-quality-v1.
- Mode: fixed_evidence.
- Requested model: gemini-3.5-flash-lite.
- HTTP timeout setting: 60 seconds.
- Input-byte limit: 64000.
- Runner retries: 0.
- Adapter retries: 0.
- Existing answer contract and automatic validation.
- Existing case criteria.
- Existing fixed evidence packets.
- Existing generation configuration other than system instruction.
- No retrieval or graph expansion.

Before execution, verify that suite data, evidence hashes, baseline
instruction, and relevant generation configuration match the recorded
baseline or explicitly document any difference.

If an unplanned difference is found, pause rather than treating
the run as the planned comparison.

## Isolation requirements

The candidate must be available through an explicit evaluation-only
selection mechanism.

The existing Production instruction and default behavior must remain
unchanged.

The implementation must record the selected instruction identity
and the SHA-256 of the actual instruction used.

No implementation mechanism is approved by this document.
Inspect the existing generator, CLI, runner, and tests before choosing
the smallest suitable change.

Add local tests for instruction selection, unchanged defaults,
and execution metadata before requesting network execution.

## Proposed comparison design

Use a fresh baseline-instruction run and a candidate-instruction run
for each of the eight cases.

The historical reports remain a reference. They do not replace
the fresh baseline arm.

Use this fixed case order:

1. answer-q1
2. answer-paraphrase-p1
3. answer-q2
4. answer-paraphrase-p2
5. answer-q5
6. answer-q6
7. answer-negative-n1
8. answer-negative-n3

For odd-numbered cases, run baseline then candidate.
For even-numbered cases, run candidate then baseline.

Run sequentially, not concurrently.

This design provides one planned invocation per case per arm.
It does not establish repeatability or statistical significance.

## Proposed network budget and stopping rules

The proposed maximum is 16 evaluation invocations:
eight cases multiplied by two instruction arms.

Network execution requires separate explicit approval after
implementation and local tests.

Before each invocation, check that the process API key is nonblank,
the output directory exists, and the destination does not exist.
Do not print the key.

Do not automatically retry any failed invocation.

Pause the sequence after any execution error, missing report,
validation failure, or unexpected metadata difference.

A semantically nonconforming but structurally valid answer is an
experimental result, not a reason to replace the sample or stop
the remaining planned semantic comparison.

Any replacement invocation requires a separately documented decision
and, if it increases the approved budget, fresh approval.

## Report retention

Every invocation must have a unique destination.

Retain all reports, including execution and validation failures.
Do not overwrite or replace an unfavorable result.

Record any invocation that produces no report separately, without
inventing timestamps, evidence hashes, or provider outcomes.

Do not modify original manual_review fields as part of this experiment.
Record AI-assisted assessments in a separate experiment review document.

## Assessment

Apply the existing draft case criteria to both arms without changing
them after seeing results.

Keep these dimensions separate:

- Execution outcome.
- Automatic validation.
- AI-assisted semantic assessment.
- Wording caveats.
- Project-author review or approval, if explicitly provided.

For each case, record both arm outcomes and the supporting answer text.

Primary questions:

1. Does the candidate satisfy the existing semantic requirements
   for answer-q5 and answer-paraphrase-p2?
2. Does either fresh baseline result differ from the historical result?
3. Does the candidate introduce a semantic regression in another case?
4. Are wording caveats preserved, reduced, or replaced by other issues?

A semantic regression means that the baseline arm meets a case's
draft criteria while the candidate arm does not.

If an arm fails to return an assessable answer, mark the semantic
comparison unavailable. Do not count execution failure as a semantic
pass or failure.

## Interpretation and decision boundaries

Do not claim improvement merely because the candidate returns
a successful answer where a historical baseline answer failed.

Consider the fresh baseline arm, all cases, and all execution outcomes.

Even if both target cases meet the criteria and no regression is
observed, describe the result only as a favorable observation on this
known set under this run design.

An inconclusive comparison remains inconclusive.

Do not promote the candidate to Production automatically.
Any adoption decision requires a separate review.

## Completion criteria

This planning step is complete when:

- The candidate wording and comparison design have been reviewed.
- The proposed budget and stopping rules are documented.
- Unchanged criteria and Production boundaries are explicit.
- The plan is committed separately from implementation.

The experiment itself is complete only after the approved sequence
has finished, or a documented decision has closed a paused sequence,
and all available outcomes have been reviewed and recorded.
