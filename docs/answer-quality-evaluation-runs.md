# Fixed-evidence answer evaluation run reviews

## Status and scope

This document records execution outcomes and AI-assisted semantic reviews
of selected live evaluation attempts using the draft answer-quality-v1
rubric.

These assessments are not independent scholarly reviews, project-author
approval of the rubric, or evidence of general model quality.

Original JSON reports remain unchanged. Their manual_review fields
remain null. This document does not implement a validated manual-review
entry or storage workflow.

Automatic checks cover answer structure, passage-ID membership,
and allowed answer status. They do not establish semantic fidelity.

The reports are stored locally under the ignored exports/ directory.
They are not committed to the repository. The identities below allow
a local report to be matched by case ID, execution timestamp,
and evidence hash.

## Summary

| Case ID              | Attempt               | UTC start                        | Automatic checks        | AI-assisted semantic assessment               |
| -------------------- | --------------------- | -------------------------------- | ----------------------- | --------------------------------------------- |
| answer-negative-n3   | Initial               | 2026-11-04T13:29:46.662238+00:00 | Passed                  | Meets the current draft case criteria         |
| answer-q5            | Initial               | 2026-11-05T09:47:13.641754+00:00 | Passed                  | Does not meet the current draft case criteria |
| answer-q1            | Initial               | 2026-11-05T12:21:07.584697+00:00 | Not performed: HTTP 503 | Not assessable: no answer returned            |
| answer-q1            | Separate manual retry | 2026-11-05T12:23:54.853712+00:00 | Passed                  | Meets the current draft case criteria         |
| answer-paraphrase-p1 | Initial               | 2026-11-05T12:26:59.818864+00:00 | Not performed: HTTP 503 | Not assessable: no answer returned            |

Five attempts cover four distinct cases.

Three attempts returned answers that passed automatic checks.
Of those answers, two meet the current draft semantic criteria
and one does not, according to AI-assisted review.

Two attempts ended with HTTP 503 and produced no answer.
These are execution failures, not semantic failures.

This is not a complete eight-case evaluation or a statistical estimate
of reliability. The q1/paraphrase-p1 contrast remains incomplete because
paraphrase-p1 has not returned an assessable answer.

## Shared execution context

- Suite: answer-quality-v1.
- Mode: fixed_evidence.
- Requested provider: Gemini.
- Requested model ID for every attempt: gemini-3.5-flash-lite.
- The serving-model version was not captured by the adapter.
- Runner retries within each attempt: 0.
- Adapter retries within each attempt: 0.
- HTTP timeout setting: 60 seconds, not a total evaluation deadline.
- Input-byte limit: 64000.
- Retrieval membership lists were empty.
- No retrieval or graph expansion was performed by the evaluation command.

The second q1 attempt was a separate manual invocation after an HTTP 503.
It was not an automatic retry within the first attempt.

System instruction SHA-256 for every attempt:

```text
da9f8bf938a147e993c38a66ff4e829adcc44effa5c0dd1452c901cbba87b4d2
```

## Run: answer-negative-n3

### Identity

- Attempt: initial.
- UTC start: 2026-11-04T13:29:46.662238+00:00.
- UTC finish: 2026-11-04T13:29:50.112918+00:00.
- Generator-call duration: approximately 3.45 seconds.
- CLI exit code: 0.
- Report error: null.

Evidence SHA-256:

```text
56fa0f2f75cc95f8dfa2788262a4e4d7d99fca59081edda045677e9c8f33185c
```

### Question and evidence

Question:

> What experimental evidence supports quantum entanglement?

Supplied passage IDs:

- passage:cusanus:ddi:1.4:la
- passage:cusanus:ddi:1.1:la
- passage:mill:on-liberty:1:harm:en

### Observed answer

Status: insufficient_evidence.

Claims: empty.

Limitation:

> The provided passages contain excerpts from Cusanus and John Stuart Mill regarding philosophy and liberty, but they do not contain any information about quantum entanglement or its experimental evidence.

### Assessment

The answer meets the current draft case criteria:

- It identifies the absence of the requested experimental information
  in the supplied passages.
- It does not answer from background physics knowledge.
- It does not present philosophical terminology as experimental evidence.
- It does not infer that experimental evidence is absent everywhere.

All automatic checks passed. With no claims, reference validity means
that no out-of-packet references occur; it does not demonstrate the
ability to support substantive claims with citations.

This is an AI-assisted assessment of the supplied report.
Project-author semantic approval has not been recorded.

## Run: answer-q5

### Identity

- Attempt: initial.
- UTC start: 2026-11-05T09:47:13.641754+00:00.
- UTC finish: 2026-11-05T09:47:15.574219+00:00.
- Generator-call duration: approximately 1.93 seconds.
- CLI exit code: 0.
- Report error: null.

Evidence SHA-256:

```text
98a387236160041316d3f2c0983e775be9973f62c59c3694c635b2a04ba6507b
```

### Question and evidence

Question:

> How is becoming related to being and nothing?

Supplied passage ID:

- passage:hegel:wl:being:de

Supplied text:

> Das Werden, Entstehen und Vergehen, ist die Ungetrenntheit des Seyns und Nichts; nicht die Einheit, welche vom Seyn und Nichts abstrahirt; sondern als Einheit des Seyns und Nichts ist es diese bestimmte Einheit.

### Observed answer

Status: answered.

Claim:

> Becoming (Das Werden, Entstehen und Vergehen) is characterized as the undivideness (Ungetrenntheit) of being and nothing, and as this specific unity rather than an abstract unity derived from them.

Referenced passage ID:

- passage:hegel:wl:being:de

Limitations: empty.

### Assessment

The answer does not meet the current draft case criteria.

It conveys the inseparability of being and nothing and identifies
a specific unity. However, it replaces the contrast with a unity
that abstracts from being and nothing with the phrase
"an abstract unity derived from them".

The source phrase is:

> nicht die Einheit, welche vom Seyn und Nichts abstrahirt

"Derived from" does not preserve "abstracts from", including within
the negative contrast introduced by "rather than".

This fails the second required semantic point and violates the
explicit prohibition against replacing "abstracts from" with
"derived from" or "originates from".

The word "undivideness" is also awkward English, but it is not the
decisive reason for the failed assessment.

No thesis-antithesis-synthesis account or historical-influence claim
was added.

All automatic checks passed because:

- The output has valid answer structure.
- Its passage ID belongs to the supplied packet.
- The status answered is allowed by the case.

Those checks do not detect the semantic substitution.

This is an AI-assisted assessment of the supplied report.
Project-author semantic approval has not been recorded.

## Run: answer-q1, initial attempt

### Identity

- Attempt: initial.
- UTC start: 2026-11-05T12:21:07.584697+00:00.
- UTC finish: 2026-11-05T12:21:16.985257+00:00.
- Generator-call duration: approximately 9.40 seconds.
- CLI exit code: 1.

Evidence SHA-256:

```text
e540f483a30a4f01b68cc3bc5e4bbd45d8dc17411b4620c824fab99c0c969671
```

### Question and evidence

Question:

> Why should a person be treated as an end rather than merely as a means?

Supplied passage ID:

- passage:kant:groundwork:2:humanity:en

### Observed outcome

Error stage: generation.

Error type: GeminiAnswerGeneratorError.

Error message:

> Gemini generation request failed (HTTP 503).

Both draft_answer and answer are null.
All automatic check values are null: the checks were not performed.

### Assessment

No answer is available for semantic review.
Record this attempt as an execution failure, not as a failed semantic
answer or an insufficient_evidence response.

The HTTP status is retained, but the provider response body is not.
The exact server-side cause cannot be established from this report.

The report remains part of the record despite the later successful
manual retry.

## Run: answer-q1, separate manual retry

### Identity

- Attempt: separate manual retry after the initial HTTP 503.
- UTC start: 2026-11-05T12:23:54.853712+00:00.
- UTC finish: 2026-11-05T12:23:57.602427+00:00.
- Generator-call duration: approximately 2.75 seconds.
- CLI exit code: 0.
- Report error: null.

Evidence SHA-256:

```text
e540f483a30a4f01b68cc3bc5e4bbd45d8dc17411b4620c824fab99c0c969671
```

### Question and evidence

Question:

> Why should a person be treated as an end rather than merely as a means?

Supplied passage ID:

- passage:kant:groundwork:2:humanity:en

Supplied text:

> Accordingly the practical imperative will be as follows: So act as to treat humanity, whether in thine own person or in that of any other, in every case as an end withal, never as means only.

### Observed answer

Status: partial.

Claim:

> A person (humanity, whether in one's own person or in that of any other) should in every case be treated as an end withal, and never as means only, according to the practical imperative.

Referenced passage ID:

- passage:kant:groundwork:2:humanity:en

Limitation:

> The provided passage states the practical imperative that a person should be treated as an end rather than merely as a means, but it does not explain why this principle holds.

### Assessment

The answer meets the current draft criteria for partial status:

- It accurately restates the humanity-as-end principle.
- It preserves never merely as a means through never as means only.
- It explicitly identifies the absence of the requested justification.
- It does not present the restatement as a complete explanation.
- It does not add an unsupported argument from dignity, rational nature,
  autonomy, or intrinsic worth.

All automatic checks passed.

The source review status remains candidate.
This assessment does not independently verify the quotation or edition.

This is an AI-assisted assessment of the supplied report.
Project-author semantic approval has not been recorded.

## Run: answer-paraphrase-p1, initial attempt

### Identity

- Attempt: initial.
- UTC start: 2026-11-05T12:26:59.818864+00:00.
- UTC finish: 2026-11-05T12:27:01.994762+00:00.
- Generator-call duration: approximately 2.18 seconds.
- CLI exit code: 1.

Evidence SHA-256:

```text
e540f483a30a4f01b68cc3bc5e4bbd45d8dc17411b4620c824fab99c0c969671
```

### Question and evidence

Question:

> Как следует поступать с другим человеком, чтобы не превращать его лишь в инструмент своих целей?

Supplied passage ID:

- passage:kant:groundwork:2:humanity:en

The evidence hash matches both q1 attempts. The question and case criteria
differ; the evidence hash does not identify the complete experiment.

### Observed outcome

Error stage: generation.

Error type: GeminiAnswerGeneratorError.

Error message:

> Gemini generation request failed (HTTP 503).

Both draft_answer and answer are null.
All automatic check values are null: the checks were not performed.

### Assessment

No answer is available for semantic review.
Record this attempt as an execution failure, not a semantic failure.

The Russian rendering, preservation of merely or only, and distinction
between a generated explanation and a published translation could not
be assessed.

The q1/paraphrase-p1 contrast remains incomplete.
Do not infer a difference in semantic performance from the HTTP failure.

## Follow-up boundaries

Retain all original reports unchanged, including execution failures.

A separate manual retry after an execution error must remain a distinct
attempt with its own timestamp and report.

Do not retry a failed semantic case solely to replace the observed
result with a successful sample.

Do not weaken the rubric to accommodate the observed wording.

No prompt, adapter, Production setting, corpus review status,
or rubric approval status is changed by this review log.

Any future prompt experiment should be reported as a separate run
with its own execution metadata and system instruction hash.
