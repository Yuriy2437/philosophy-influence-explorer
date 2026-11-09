# Fixed-evidence answer evaluation run reviews

## Status and scope

This document records execution outcomes and AI-assisted semantic reviews
of live evaluation attempts using the draft answer-quality-v1 rubric.

These assessments are not independent scholarly reviews, project-author
approval of the rubric, or evidence of general model quality.

Original JSON reports remain unchanged. Their manual_review fields
remain null. This document does not implement a validated manual-review
entry or storage workflow.

Automatic checks cover answer structure, passage-ID membership,
and allowed answer status. They do not establish semantic fidelity.

Reports are stored locally under the ignored exports/ directory.
They are not committed to the repository. Match a local report using
case ID, execution timestamp, and evidence hash.

## Summary

| Case ID              | Attempt                                               | UTC start                           | Automatic checks               | AI-assisted semantic assessment                 |
| -------------------- | ----------------------------------------------------- | ----------------------------------- | ------------------------------ | ----------------------------------------------- |
| answer-negative-n3   | Initial                                               | 2026-11-04T13:29:46.662238+00:00    | Passed                         | Meets draft criteria                            |
| answer-q5            | Initial                                               | 2026-11-05T09:47:13.641754+00:00    | Passed                         | Does not meet draft criteria                    |
| answer-q1            | Initial                                               | 2026-11-05T12:21:07.584697+00:00    | Not performed: HTTP 503        | Not assessable                                  |
| answer-q1            | Separate manual retry                                 | 2026-11-05T12:23:54.853712+00:00    | Passed                         | Meets draft criteria                            |
| answer-paraphrase-p1 | Initial                                               | 2026-11-05T12:26:59.818864+00:00    | Not performed: HTTP 503        | Not assessable                                  |
| answer-paraphrase-p1 | Separate manual retry                                 | 2026-11-05T12:51:04.336366+00:00    | Passed                         | Meets core draft criteria with a wording caveat |
| answer-q2            | Initial                                               | 2026-11-05T13:19:40.434260+00:00    | Passed                         | Meets draft criteria                            |
| answer-paraphrase-p2 | Initial                                               | 2026-11-05T13:24:04.966754+00:00    | Passed                         | Does not meet draft criteria                    |
| answer-q6            | Initial                                               | 2026-11-05T13:25:50.320847+00:00    | Passed                         | Meets draft criteria with a wording caveat      |
| answer-negative-n1   | Initial                                               | 2026-11-05T13:27:50.560560+00:00    | Not performed: HTTP 503        | Not assessable                                  |
| answer-negative-n1   | Separate manual retry                                 | 2026-11-05T13:29:41.608452+00:00    | Not performed: HTTP 503        | Not assessable                                  |
| answer-negative-n1   | Separate manual retry; local setup failure            | Not recorded; local date 2026-11-09 | Not performed: missing API key | Not assessable; no report                       |
| answer-negative-n1   | Separate manual retry after environment configuration | 2026-11-09T07:07:27.768701+00:00    | Passed                         | Meets draft criteria                            |

Thirteen CLI invocations cover all eight distinct cases.
Twelve JSON reports were saved. One invocation stopped during local
setup because GOOGLE_API_KEY was absent, before any provider request
or report generation.

Eight invocations returned answers, all of which passed automatic checks.
AI-assisted review assessed four answers as meeting the draft criteria
without a noted wording caveat, two as meeting them with wording caveats,
and two as not meeting them.

Four invocations ended with HTTP 503 and saved reports without answers.
These are execution failures, not semantic failures.
The missing-key invocation is a separate local setup failure.

Each of the eight distinct cases now has one returned answer and
an AI-assisted semantic assessment.

The q1/paraphrase-p1 contrast has been observed in returned answers:
q1 returned partial with a missing-justification limitation, while
paraphrase-p1 returned answered with a Russian restatement of the principle.

The successful negative-n1 invocation returned insufficient_evidence
with no claims and an explicit explanation of the missing comparison.

This completes case coverage for the recorded fixed-evidence series.
It is not repeated-sample testing, end-to-end answer-workflow evaluation,
a statistical estimate of reliability, or evidence of stable behavior.

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

Retries of q1, paraphrase-p1, and negative-n1 were separate manual
invocations after execution errors. They were not automatic retries
within the preceding attempts.

System instruction SHA-256 recorded in every saved report:

```text
da9f8bf938a147e993c38a66ff4e829adcc44effa5c0dd1452c901cbba87b4d2
```

The missing-key invocation produced no execution metadata or evidence
hash. The shared settings above describe the saved evaluation reports
and requested CLI parameters, not a completed execution for that invocation.

Inspection of the CLI and generator confirmed that an empty API key
raises ValueError in the generator constructor, before evaluation,
HTTP transmission, and report generation.

For every recorded HTTP 503:

- Error stage: generation.
- Error type: GeminiAnswerGeneratorError.
- Error message: Gemini generation request failed (HTTP 503).
- Both draft_answer and answer are null.
- All automatic check values are null, meaning not performed.

The provider response body was not retained. The exact server-side
cause of these failures cannot be established from the reports.

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

> What experimental evidence supports quantum entanglement?

Supplied passage IDs:

- passage:cusanus:ddi:1.4:la
- passage:cusanus:ddi:1.1:la
- passage:mill:on-liberty:1:harm:en

### Observed answer

Status: insufficient_evidence. Claims: empty.

Limitation:

> The provided passages contain excerpts from Cusanus and John Stuart Mill regarding philosophy and liberty, but they do not contain any information about quantum entanglement or its experimental evidence.

### Assessment

Meets the current draft criteria.

The answer identifies missing experimental information in the supplied
passages. It does not introduce background physics knowledge, present
philosophical terminology as experimental evidence, or infer that
experimental evidence is absent everywhere.

With no claims, reference validity means that no out-of-packet references
occur. It does not demonstrate support for substantive cited claims.

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

> How is becoming related to being and nothing?

Supplied passage ID:

- passage:hegel:wl:being:de

Supplied text:

> Das Werden, Entstehen und Vergehen, ist die Ungetrenntheit des Seyns und Nichts; nicht die Einheit, welche vom Seyn und Nichts abstrahirt; sondern als Einheit des Seyns und Nichts ist es diese bestimmte Einheit.

### Observed answer

Status: answered. Limitations: empty.

Claim:

> Becoming (Das Werden, Entstehen und Vergehen) is characterized as the undivideness (Ungetrenntheit) of being and nothing, and as this specific unity rather than an abstract unity derived from them.

Referenced passage ID:

- passage:hegel:wl:being:de

### Assessment

Does not meet the current draft criteria.

The answer conveys inseparability and a specific unity. However,
"an abstract unity derived from them" does not preserve the contrast
with a unity that abstracts from being and nothing.

The source phrase is:

> nicht die Einheit, welche vom Seyn und Nichts abstrahirt

The negative contrast introduced by "rather than" does not correct
the substitution of derived from for abstracts from.

This fails the second required semantic point and violates the explicit
prohibition against that substitution.

"Undivideness" is awkward English but is not the decisive failure.
No thesis-antithesis-synthesis account or historical-influence claim
was added.

The valid structure, reference membership, and allowed status do not
detect the semantic error.

## Run: answer-q1, initial attempt

### Identity

- Attempt: initial.
- UTC start: 2026-11-05T12:21:07.584697+00:00.
- UTC finish: 2026-11-05T12:21:16.985257+00:00.
- Generator-call duration: approximately 9.40 seconds.
- CLI exit code: 1.
- Outcome: HTTP 503; no answer.

Evidence SHA-256:

```text
e540f483a30a4f01b68cc3bc5e4bbd45d8dc17411b4620c824fab99c0c969671
```

### Question and evidence

> Why should a person be treated as an end rather than merely as a means?

Supplied passage ID:

- passage:kant:groundwork:2:humanity:en

### Assessment

Not assessable. This is an execution failure, not a semantic failure
or an insufficient_evidence answer.

Retain this report despite the later successful manual retry.

## Run: answer-q1, separate manual retry

### Identity

- Attempt: separate manual retry after HTTP 503.
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

Meets the current draft criteria for partial status.

The answer preserves the humanity-as-end principle and never merely
as a means. It explicitly identifies the missing justification and
does not present the restatement as a complete explanation.

No unsupported argument from dignity, rational nature, autonomy,
or intrinsic worth was added.

The source review status remains candidate. This assessment does not
independently verify the quotation or edition.

## Run: answer-paraphrase-p1, initial attempt

### Identity

- Attempt: initial.
- UTC start: 2026-11-05T12:26:59.818864+00:00.
- UTC finish: 2026-11-05T12:27:01.994762+00:00.
- Generator-call duration: approximately 2.18 seconds.
- CLI exit code: 1.
- Outcome: HTTP 503; no answer.

Evidence SHA-256:

```text
e540f483a30a4f01b68cc3bc5e4bbd45d8dc17411b4620c824fab99c0c969671
```

### Question and evidence

> Как следует поступать с другим человеком, чтобы не превращать его лишь в инструмент своих целей?

Supplied passage ID:

- passage:kant:groundwork:2:humanity:en

### Assessment

Not assessable. The Russian rendering and preservation of merely
or only could not be reviewed for this attempt.

Do not infer a semantic-performance difference from the HTTP failure.
A later separate attempt returned an assessable answer.

## Run: answer-paraphrase-p1, separate manual retry

### Identity

- Attempt: separate manual retry after HTTP 503.
- UTC start: 2026-11-05T12:51:04.336366+00:00.
- UTC finish: 2026-11-05T12:51:06.243905+00:00.
- Generator-call duration: approximately 1.91 seconds.
- CLI exit code: 0.
- Report error: null.

Evidence SHA-256:

```text
e540f483a30a4f01b68cc3bc5e4bbd45d8dc17411b4620c824fab99c0c969671
```

### Question and evidence

> Как следует поступать с другим человеком, чтобы не превращать его лишь в инструмент своих целей?

Supplied passage ID:

- passage:kant:groundwork:2:humanity:en

The evidence hash matches both q1 attempts and the initial p1 attempt.
Questions and criteria differ; an evidence hash does not identify
the complete experiment.

### Observed answer

Status: answered. Limitations: empty.

Claim:

> Согласно практическому императиву, другого человека (как и самого себя) следует всегда воспринимать как цель, а не только как средство.

Referenced passage ID:

- passage:kant:groundwork:2:humanity:en

### Assessment

Meets the core draft criteria with a wording caveat.

The answer is in Russian, preserves the qualification not only as
a means, does not prohibit every instrumental interaction, and does not
claim to be a published or independently verified translation.

However, воспринимать is weaker than the source instruction
"So act as to treat". It can shift emphasis from conduct toward
perception. Обращаться с would be a more precise rendering here.

Record the caveat rather than treating the wording as fully precise.
The generated answer remains unchanged.

Together with the successful q1 retry, this provides one observed
contrast between stating a principle and supplying its justification.
It does not demonstrate stable behavior across repeated samples.

## Run: answer-q2

### Identity

- Attempt: initial.
- UTC start: 2026-11-05T13:19:40.434260+00:00.
- UTC finish: 2026-11-05T13:19:42.339977+00:00.
- Generator-call duration: approximately 1.90 seconds.
- CLI exit code: 0.
- Report error: null.

Evidence SHA-256:

```text
7332e8c697fdb44f3c9c0f3cee1fdf6361dc69e4c6263a1fcdade6ffe87d7083
```

### Question and evidence

> What does it mean for the will to give itself a universal law?

Supplied passage ID:

- passage:kant:groundwork:2:autonomy:en

### Observed answer

Status: answered. Limitations: empty.

Claim:

> For the will to give itself a universal law means that it is a law to itself independently of any property of the objects of volition, operating on the principle to always choose in such a way that the same volition comprehends the maxims of the choice as a universal law.

Referenced passage ID:

- passage:kant:groundwork:2:autonomy:en

### Assessment

Meets the current draft criteria.

The answer preserves both independence from properties of the objects
of volition and the connection between choice, maxims, and universal law.

It does not equate autonomy with arbitrary preference or supply
an unsupported broader derivation.

The wording closely follows the source rather than offering an accessible
explanation. The current case does not require examples or a separate
clarification of terminology; no new requirement is imposed retrospectively.

The source review status remains candidate.

## Run: answer-paraphrase-p2

### Identity

- Attempt: initial.
- UTC start: 2026-11-05T13:24:04.966754+00:00.
- UTC finish: 2026-11-05T13:24:06.486624+00:00.
- Generator-call duration: approximately 1.52 seconds.
- CLI exit code: 0.
- Report error: null.

Evidence SHA-256:

```text
16304f1b73ccf819cf0e36113a3825c80caf58ec5c96d65f69613254bf46a1f8
```

### Question and evidence

> Is someone's own good enough to justify forcing them to act, or must other people be at risk?

Supplied passage ID:

- passage:mill:on-liberty:1:harm:en

### Observed answer

Status: answered. Limitations: empty.

Claim:

> Power can only be rightfully exercised over a member of a civilized community against their will to prevent harm to others, meaning someone's own good is not sufficient justification.

Referenced passage ID:

- passage:mill:on-liberty:1:harm:en

### Assessment

Does not meet the current draft criteria because a required limitation
is missing.

The answer preserves the main distinction and the quoted scope.
It does not explicitly claim that any risk justifies any coercive measure.

However, it does not explain that identifying the permissible purpose
does not establish the sufficiency of any particular risk or proposed
coercive measure. The case explicitly requires that limitation.

This is an omission, not an observed assertion that every coercive
measure is justified.

An empty limitations array is not by itself decisive: equivalent wording
elsewhere in the answer could satisfy the semantic requirement.
Here, the required clarification is absent throughout the answer.

The source review status remains candidate.

## Run: answer-q6

### Identity

- Attempt: initial.
- UTC start: 2026-11-05T13:25:50.320847+00:00.
- UTC finish: 2026-11-05T13:25:59.011050+00:00.
- Generator-call duration: approximately 8.69 seconds.
- CLI exit code: 0.
- Report error: null.

Evidence SHA-256:

```text
15c71d5239e50d66378ed198dbaa5c5cd6ae6963ae57c54b8fe145f8eb843462
```

### Question and evidence

> Почему бесконечное нельзя постичь через сравнение и пропорцию?

Supplied passage ID:

- passage:cusanus:ddi:1.1:la

### Observed answer

Status: answered. Limitations: empty.

Claim:

> Бесконечное ускользает от любой пропорции, в то время как любая познавательная деятельность легка в сравнительной пропорциональной связи и трудна при достижении бесконечного, поэтому бесконечное непостижимо.

Referenced passage ID:

- passage:cusanus:ddi:1.1:la

### Assessment

Meets the current draft criteria with a wording caveat.

The answer preserves ease within comparative proportional relations,
difficulty when reaching the infinite, and the stated inference from
escaping every proportion to incomprehensibility.

It adds no mathematical proof or broader theory of finite intellect.
It does not claim that all meaningful statements about the infinite
are impossible or present the Russian text as a published translation.

Любая познавательная деятельность is broader and less precise than
исследование for inquisitio. In this sentence, the conditions and
argumentative connection remain present. Record the wording caveat
without treating a required semantic point as lost.

The final statement of incomprehensibility remains connected to
the preceding proportional-comparison explanation.

## Run: answer-negative-n1, initial attempt

### Identity

- Attempt: initial.
- UTC start: 2026-11-05T13:27:50.560560+00:00.
- UTC finish: 2026-11-05T13:27:52.082892+00:00.
- Generator-call duration: approximately 1.53 seconds.
- CLI exit code: 1.
- Outcome: HTTP 503; no answer.

Evidence SHA-256:

```text
5362bb749dd4a98849a54d5ac8fc46aace407a2dd6e53435a1e772f7144bd0b1
```

### Question and evidence

> How does Kant distinguish a hypothetical imperative from a categorical imperative?

Supplied passage IDs:

- passage:kant:groundwork:2:humanity:en
- passage:kant:groundwork:2:autonomy:en

### Assessment

Not assessable. This is an execution failure, not a semantic failure
or a successful insufficient_evidence answer.

The intended test of refusing an unsupported comparison could not
be assessed.

## Run: answer-negative-n1, separate manual retry

### Identity

- Attempt: separate manual retry after HTTP 503.
- UTC start: 2026-11-05T13:29:41.608452+00:00.
- UTC finish: 2026-11-05T13:29:47.845298+00:00.
- Generator-call duration: approximately 6.24 seconds.
- CLI exit code: 1.
- Outcome: HTTP 503; no answer.

Evidence SHA-256:

```text
5362bb749dd4a98849a54d5ac8fc46aace407a2dd6e53435a1e772f7144bd0b1
```

### Question and evidence

> How does Kant distinguish a hypothetical imperative from a categorical imperative?

Supplied passage IDs:

- passage:kant:groundwork:2:humanity:en
- passage:kant:groundwork:2:autonomy:en

### Assessment

Not assessable. A second execution failure does not establish that
the question or its content caused the server error.

Network attempts were paused after this failure. Later separate
invocations on 2026-11-09 are recorded below; this failed report
remains unchanged.

## Invocation: answer-negative-n1, local setup failure

### Identity

- Attempt: separate manual retry; filename label retry2.
- Local date: 2026-11-09.
- Exact UTC start and finish: not recorded.
- CLI exit code: 2.
- JSON report: not created.
- Provider request: not made.

The intended output path was:

```text
exports/answer-negative-n1-retry2-20261109-094745-d88707ff.json
```

The timestamp in this filename was generated when constructing the path.
It is not a recorded evaluation start timestamp.

### Observed outcome

The CLI printed:

> Evaluation setup or report saving failed. Check case ID, model, GOOGLE_API_KEY, limits, and output path. A saving failure may occur after the provider call.

A subsequent environment check showed:

- GOOGLE_API_KEY was absent or blank in the current process.
- The exports directory existed.
- The intended report file did not exist.

Source inspection confirmed that the CLI passes the process environment
value directly to GeminiAnswerGenerator. Its constructor rejects an empty
key with ValueError before run_answer_evaluation and before any HTTP call.

### Assessment

Not assessable. This was a local configuration failure, not an HTTP 503,
a provider response, or a semantic failure.

No answer, automatic-check results, evidence hash, or execution metadata
were produced. Do not assign this invocation the evidence hash from
another attempt.

The API key was subsequently supplied to the process environment.
No source-code change was required.

## Run: answer-negative-n1, successful separate manual retry

### Identity

- Attempt: separate manual retry after environment configuration;
  filename label retry3.
- UTC start: 2026-11-09T07:07:27.768701+00:00.
- UTC finish: 2026-11-09T07:07:29.174467+00:00.
- Generator-call duration: approximately 1.41 seconds.
- CLI exit code: 0.
- Report error: null.
- All automatic checks: passed.

Evidence SHA-256:

```text
5362bb749dd4a98849a54d5ac8fc46aace407a2dd6e53435a1e772f7144bd0b1
```

This matches the evidence hash in both earlier negative-n1 reports.
The requested model and recorded system instruction hash also match
the earlier reports. The serving-model version was not captured.

### Question and evidence

> How does Kant distinguish a hypothetical imperative from a categorical imperative?

Supplied passage IDs:

- passage:kant:groundwork:2:humanity:en
- passage:kant:groundwork:2:autonomy:en

### Observed answer

Status: insufficient_evidence.

Claims: empty.

Limitation:

> The supplied passages discuss the practical imperative regarding humanity as an end and the autonomy of the will, but they do not contain any information distinguishing a hypothetical imperative from a categorical imperative.

The draft_answer and answer fields contain the same structured response.

### Assessment

Meets the current draft case criteria.

The answer uses the only allowed status, makes no claims, and identifies
the specific evidence gap: the supplied excerpts discuss humanity as
an end and autonomy but do not provide the requested distinction.

It does not introduce the missing comparison from background knowledge
or treat thematic relevance as sufficient support.

The limitation concerns the supplied passages, not the whole work
or Kant's philosophy generally.

With no claims, reference validity means that no out-of-packet references
occur. It does not demonstrate support for substantive cited claims.

This is an AI-assisted assessment. Project-author semantic approval
has not been recorded. The original report remains unchanged,
with manual_review fields null.

## Findings and limitations

All eight returned answers passed automatic checks, but AI-assisted
review identified two semantic nonconformities:

- q5 substitutes derived from for abstracts from.
- paraphrase-p2 omits an explicitly required limitation.

Two other answers have recorded wording caveats:

- paraphrase-p1 uses воспринимать where conduct-oriented wording
  would be more precise.
- q6 uses любая познавательная деятельность rather than исследование.

The available q1 and paraphrase-p1 answers show the intended distinction
between a justification question and a question asking how to act.

Execution availability and semantic quality remain separate dimensions.
The four HTTP 503 attempts do not count as semantic failures or passes.

The local missing-key invocation also counts as neither a semantic
failure nor a pass. It made no provider request and produced no report.

Negative-n1 now has an assessable answer meeting the draft criteria.
All eight cases have one returned answer and an AI-assisted assessment;
this does not establish repeatability or project-author approval.

These selected observations are not a benchmark score, an estimate
of provider-wide availability, or project-author semantic approval.

## Follow-up boundaries

Retain all original reports unchanged, including execution failures.

A separate manual retry after an execution error must remain a distinct
attempt with its own timestamp and report.

Do not retry a failed semantic case solely to replace the observed
result with a successful sample.

Do not weaken the rubric to accommodate the observed wording.

Network attempts were paused after the second negative-n1 HTTP 503
and resumed separately on 2026-11-09.

The recorded series now has a returned answer and AI-assisted assessment
for every case. No further network calls are needed to complete this
case-coverage step.

Do not describe this coverage as project-author semantic approval,
repeated-sample validation, or end-to-end workflow evaluation.

No prompt, adapter, Production setting, corpus review status,
or rubric approval status is changed by this review log.

Any future prompt experiment should be reported as a separate run
with its own execution metadata and system instruction hash.
