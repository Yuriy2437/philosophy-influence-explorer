# Fixed-evidence prompt experiment review

## Status and scope

This document records the completed semantic-fidelity-v1 instruction
experiment and AI-assisted assessments of its returned answers.

These assessments are not independent scholarly reviews, project-author
semantic approval, or approval of the draft answer-quality-v1 rubric.

The experiment evaluates fixed-evidence answer generation on a known set.
It does not evaluate retrieval, graph expansion, or the end-to-end workflow.

Original JSON reports remain unchanged. Their manual_review fields
remain null. Reports are stored locally under the ignored exports/
directory and are not committed.

## Plan and implementation

- Plan: [prompt experiment plan](answer-quality-prompt-experiment-plan.md).
- Plan commit: 1b8a439.
- Implementation commit used for execution: ced9c86.
- Historical baseline documentation commit: 5adf991.
- Historical observations: [run review log](answer-quality-evaluation-runs.md).
- Execution date: 2026-11-10.
- The user confirmed Free Tier before the first experiment request.
- The user authorized a maximum of 16 sequential evaluation invocations.
- This review does not independently verify billing or monetary charges.

All 16 planned invocations completed in the specified order.
No replacement samples, automatic retries, or additional experiment
requests were made in this sequence.

## Instruction identities

Baseline ID: baseline.

Baseline SHA-256:

```text
da9f8bf938a147e993c38a66ff4e829adcc44effa5c0dd1452c901cbba87b4d2
```

Baseline UTF-8 length: 1290 bytes.

Candidate ID: semantic-fidelity-v1.

Candidate SHA-256:

```text
5f7d4830fcbb69bb0eedad96d32cac99e787b187684d9d41c8076a41c8d4f63c
```

Candidate UTF-8 length: 1811 bytes.

The candidate contains the unchanged baseline, one blank line,
and the exact addition recorded in the plan.

The instruction hashes in all reports match the selected variants.
The baseline constant was not replaced.

## Execution conditions and preflight

- Suite: answer-quality-v1.
- Mode: fixed_evidence.
- Provider: Gemini.
- Requested model: gemini-3.5-flash-lite.
- HTTP timeout: 60 seconds, not a total evaluation deadline.
- Input-byte limit: 64000.
- Runner retries: 0.
- Adapter retries: 0.
- No retrieval or graph expansion.
- Retrieval membership lists: empty.
- Existing answer contract and case criteria: unchanged.
- Existing generation configuration other than system instruction: unchanged.

Before execution, comparison of tracked data against 5adf991 returned
no differences. The generator diff contained only instruction injection
and validation changes.

The serving-model version was not captured. Matching the requested
model ID does not establish an unchanged serving-model version.

Local checks before execution passed:

- 63 targeted tests.
- 432 tests in the complete suite, with one dependency deprecation warning.

## Execution record

B means baseline. C means semantic-fidelity-v1.

Every invocation below:

- Saved one JSON report.
- Returned CLI exit code 0.
- Had report error null.
- Passed all three automatic checks.
- Left manual_review fields null.

Durations measure the generator call and are rounded to two decimals.

| No. | Case                 | Arm | UTC start                        | Duration, seconds | Status                | AI-assisted assessment                     |
| --- | -------------------- | --- | -------------------------------- | ----------------: | --------------------- | ------------------------------------------ |
| 01  | answer-q1            | B   | 2026-11-10T06:47:04.140510+00:00 |              4.97 | partial               | Meets draft criteria                       |
| 02  | answer-q1            | C   | 2026-11-10T06:53:01.921846+00:00 |              1.92 | partial               | Meets draft criteria                       |
| 03  | answer-paraphrase-p1 | C   | 2026-11-10T06:55:06.795755+00:00 |              2.79 | answered              | Meets draft criteria                       |
| 04  | answer-paraphrase-p1 | B   | 2026-11-10T07:02:17.482460+00:00 |              2.11 | answered              | Meets draft criteria                       |
| 05  | answer-q2            | B   | 2026-11-10T07:04:53.327361+00:00 |              4.60 | answered              | Meets draft criteria                       |
| 06  | answer-q2            | C   | 2026-11-10T07:07:34.975222+00:00 |              1.84 | answered              | Meets draft criteria with a wording caveat |
| 07  | answer-paraphrase-p2 | C   | 2026-11-10T07:09:47.535502+00:00 |              1.60 | answered              | Does not meet draft criteria               |
| 08  | answer-paraphrase-p2 | B   | 2026-11-10T07:12:26.660895+00:00 |              1.83 | answered              | Does not meet draft criteria               |
| 09  | answer-q5            | B   | 2026-11-10T07:14:32.498039+00:00 |              4.41 | answered              | Meets draft criteria with wording caveats  |
| 10  | answer-q5            | C   | 2026-11-10T07:16:36.975161+00:00 |              5.68 | answered              | Does not meet draft criteria               |
| 11  | answer-q6            | C   | 2026-11-10T07:19:24.932585+00:00 |              1.66 | answered              | Does not meet draft criteria               |
| 12  | answer-q6            | B   | 2026-11-10T07:21:29.830628+00:00 |              6.90 | answered              | Does not meet draft criteria               |
| 13  | answer-negative-n1   | B   | 2026-11-10T07:23:42.055543+00:00 |              5.05 | insufficient_evidence | Meets draft criteria                       |
| 14  | answer-negative-n1   | C   | 2026-11-10T07:25:35.239166+00:00 |              4.54 | insufficient_evidence | Meets draft criteria                       |
| 15  | answer-negative-n3   | C   | 2026-11-10T07:27:22.478383+00:00 |              5.05 | insufficient_evidence | Meets draft criteria                       |
| 16  | answer-negative-n3   | B   | 2026-11-10T07:29:45.327111+00:00 |              1.64 | insufficient_evidence | Meets draft criteria                       |

Reports can be matched locally by sequence number, case ID, arm,
UTC execution timestamp, and evidence hash. Filename creation times
are not execution start timestamps.

No speed advantage is inferred from individual call durations.

## Evidence identities

Evidence hashes match the corresponding historical packets.
The same packet was used for both arms of each case.

### q1 and paraphrase-p1

```text
e540f483a30a4f01b68cc3bc5e4bbd45d8dc17411b4620c824fab99c0c969671
```

### q2

```text
7332e8c697fdb44f3c9c0f3cee1fdf6361dc69e4c6263a1fcdade6ffe87d7083
```

### paraphrase-p2

```text
16304f1b73ccf819cf0e36113a3825c80caf58ec5c96d65f69613254bf46a1f8
```

### q5

```text
98a387236160041316d3f2c0983e775be9973f62c59c3694c635b2a04ba6507b
```

### q6

```text
15c71d5239e50d66378ed198dbaa5c5cd6ae6963ae57c54b8fe145f8eb843462
```

### negative-n1

```text
5362bb749dd4a98849a54d5ac8fc46aace407a2dd6e53435a1e772f7144bd0b1
```

### negative-n3

```text
56fa0f2f75cc95f8dfa2788262a4e4d7d99fca59081edda045677e9c8f33185c
```

An evidence hash identifies the packet, not the question, rubric,
instruction, serving-model version, or complete experiment.

## Pair reviews and returned answer text

The following quotations reproduce claim and limitation text
from the accepted answer fields. Passage IDs and full evidence
remain available in the original reports.

### q1

Question:

> Why should a person be treated as an end rather than merely as a means?

Baseline claim:

> The practical imperative states that humanity, whether in one's own person or that of another, must be treated in every case as an end and never as a means only.

Baseline limitation:

> The supplied passages state the practical imperative that a person should be treated as an end rather than merely as a means, but they do not provide the explanation or reasoning of why this principle holds.

Candidate claim:

> The practical imperative dictates that a person should be treated as an end in every case, and never merely as a means.

Candidate limitation:

> The supplied passages state the principle that a person should be treated as an end rather than merely as a means, but they do not provide the explanation or reason why a person should be treated this way.

Both meet the draft criteria for partial status.

Both preserve never merely as a means, explicitly identify the missing
justification, and avoid supplying unsupported arguments from dignity,
rational nature, autonomy, or intrinsic worth.

No candidate improvement or regression is observed on this pair.

### paraphrase-p1

Question:

> Как следует поступать с другим человеком, чтобы не превращать его лишь в инструмент своих целей?

Candidate claim:

> Согласно практическому императиву, следует относиться к человечеству как в своем собственном лице, так и в лице любого другого всегда как к цели и никогда только как к средству.

Baseline claim:

> Согласно практическому императиву, следует относиться к человечеству в лице любого другого человека всегда как к цели, и никогда — только как к средству.

Both have status answered and empty limitations.

Both meet the draft criteria. They preserve the qualification only,
do not prohibit all instrumental interaction, and do not claim to be
published or independently verified translations.

The candidate includes the self as well as others, supported by the
passage. The baseline focuses on the other person asked about.

Both use относиться rather than the historical answer's воспринимать.
The historical wording caveat is absent in both fresh arms and cannot
be attributed specifically to the candidate.

No candidate improvement or regression is observed on this pair.

### q2

Question:

> What does it mean for the will to give itself a universal law?

Baseline claim 1:

> For the will to give itself a universal law means that the will is a law to itself independently of any property of the objects of volition, which is characterized as the autonomy of the will.

Baseline claim 2:

> The principle of autonomy requires choosing in such a way that the same volition comprehends the maxims of our choice as a universal law.

Candidate claim:

> For the will to give itself a universal law—which is the property of the autonomy of the will—means that the will is a law to itself independently of any property of the objects of volition, adhering to the principle to always choose in such a way that the same volition comprehends the maxims of our choice as a universal law.

Both have status answered and empty limitations.

Both meet the draft criteria. They preserve independence from properties
of the objects of volition and the connection between choice, maxims,
and universal law.

Neither equates autonomy with arbitrary preference or supplies
a broader unsupported derivation.

The candidate's phrase "the property of the autonomy of the will"
is awkward: the source defines autonomy as a property of the will.
The rest of the sentence preserves that definition sufficiently
for the current required points. Record a wording caveat, not a failed
required point.

No candidate improvement or semantic regression is observed on this pair.

### paraphrase-p2

Question:

> Is someone's own good enough to justify forcing them to act, or must other people be at risk?

Candidate claim:

> The only legitimate purpose for exercising power over a member of a civilized community against their will is to prevent harm to others.

Baseline claim:

> Power can only be rightfully exercised over a member of a civilized community against their will to prevent harm to others, meaning someone's own good is not sufficient justification.

Both have status answered and empty limitations.

Neither meets the draft criteria.

Both omit the required clarification that identifying the only
permissible purpose does not establish that any risk or any proposed
coercive measure is sufficient for justification.

The baseline explicitly rejects someone's own good as sufficient
justification. The candidate conveys this only indirectly through
the only-purpose formulation.

Both retain the passage's stated community scope. Neither explicitly
claims that every risk automatically justifies every coercive measure.
Record an omission, not an assertion absent from the answers.

The baseline claim matches the historical answer text.
The candidate did not eliminate the motivating omission in this sample.

No baseline-to-candidate semantic regression is recorded because
both arms fail the existing criteria.

### q5

Question:

> How is becoming related to being and nothing?

Baseline claim:

> Becoming (Das Werden, Entstehen und Vergehen) is the undividedeness (Ungetrenntheit) of being (Seyn) and nothing (Nichts), specifically as this determined unity rather than an abstraction from them.

Candidate claim:

> Das Werden (Entstehen und Vergehen) ist als bestimmte Einheit die Ungetrenntheit des Seyns und Nichts.

Both have status answered and empty limitations.

The baseline meets the draft criteria with wording caveats.

"Undividedeness" is awkward English. "Rather than an abstraction from
them" compresses the source's contrast with a unity that abstracts
from being and nothing, but preserves the required contrast.

Unlike the historical baseline answer, the fresh baseline does not
replace abstracts from with derived from.

The candidate does not meet the draft criteria. It conveys
inseparability and determinate unity but omits the required contrast
with a unity that abstracts from being and nothing.

The candidate also answers in German despite an English question.
This is a separate violation of the existing system instruction,
not a newly added case criterion. The semantic omission alone
is sufficient for the failed case assessment.

Neither arm adds a thesis-antithesis-synthesis account or historical
influence claim.

This pair is the experiment's one observed semantic regression:
the fresh baseline meets the case criteria and the candidate does not.

### q6

Question:

> Почему бесконечное нельзя постичь через сравнение и пропорцию?

Candidate claim 1:

> Бесконечное ускользает от любой пропорции, в то время как всякое исследование опирается на сравнительную пропорциональную связь и становится трудным при достижении бесконечного.

Candidate claim 2:

> Из-за того, что бесконечное ускользает от любой пропорции, оно является непостижимым.

Baseline claim:

> Бесконечное ускользает от любой пропорции, в то время как всякое исследование опирается на сравнительную пропорциональную связь и становится трудным при достижении бесконечного.

Both have status answered and empty limitations.

Neither meets the draft criteria.

The candidate's first claim and the baseline's sole claim are identical.
Both replace inquiry being easy within comparative proportional
relations with the stronger claim that all inquiry relies on those
relations. The required easy-versus-difficult contrast is not preserved.

The candidate explicitly states the inference from escaping every
proportion to incomprehensibility. The baseline supplies the premise
but does not explicitly complete that inference.

The candidate is more complete on the second required point,
but still fails the first. This is not a transition to case conformity.

Neither adds a mathematical proof, a published-translation claim,
or a claim that no meaningful statement about the infinite is possible.

The fresh baseline differs from the historical answer, which preserved
ease and the explicit conclusion. Historical assessments remain
unchanged because they concern different answer text.

No baseline-to-candidate semantic regression is recorded for this pair.

### negative-n1

Question:

> How does Kant distinguish a hypothetical imperative from a categorical imperative?

Both have status insufficient_evidence and empty claims.

Baseline limitation:

> The supplied passages discuss the practical imperative regarding humanity and the autonomy of the will, but they do not contain any information about how Kant distinguishes a hypothetical imperative from a categorical imperative.

Candidate limitation:

> The supplied passages discuss the practical imperative regarding humanity and the autonomy of the will, but they do not contain any text distinguishing a hypothetical imperative from a categorical imperative.

Both meet the draft criteria.

They identify the specific missing comparison and do not substitute
background knowledge or thematic relevance for supplied support.

The limitations concern the supplied passages, not the whole work
or Kant's philosophy generally.

No candidate improvement or regression is observed on this pair.

### negative-n3

Question:

> What experimental evidence supports quantum entanglement?

Both have status insufficient_evidence and empty claims.

Candidate limitation:

> The supplied passages discuss Nicholas of Cusa's philosophical concepts regarding the maximum and the infinite (passage:cusanus:ddi:1.4:la, passage:cusanus:ddi:1.1:la) and John Stuart Mill's harm principle regarding power over a community member (passage:mill:on-liberty:1:harm:en). None of the passages contain any experimental evidence or information about quantum entanglement.

Baseline limitation:

> The supplied passages do not contain any information regarding quantum entanglement or experimental evidence supporting it.

Both meet the draft criteria.

Neither supplies background physics knowledge, treats philosophical
concepts as experimental evidence, or infers that no evidence exists
outside the supplied packet.

The candidate's descriptive context serves to explain the evidence gap.
Its inline passage IDs belong to the supplied packet, but these are
free-text mentions in limitations, not structured claim references.

With empty claims, automatic reference validity does not demonstrate
validation of those free-text mentions or support for substantive claims.

No candidate improvement or regression is observed on this pair.

## Aggregate observations

| Outcome                                                  | Baseline | Candidate | Total |
| -------------------------------------------------------- | -------: | --------: | ----: |
| Returned answers                                         |        8 |         8 |    16 |
| Passed automatic checks                                  |        8 |         8 |    16 |
| Meets draft semantic criteria, including wording caveats |        6 |         5 |    11 |
| Does not meet draft semantic criteria                    |        2 |         3 |     5 |
| Execution failures                                       |        0 |         0 |     0 |

Among the answers meeting criteria, wording caveats were recorded
for baseline q5 and candidate q2.

Pair outcomes:

- Five pairs: both arms meet the draft criteria.
- Two pairs: neither arm meets them, paraphrase-p2 and q6.
- One pair: baseline meets them and candidate does not, q5.
- No pair: baseline fails and candidate meets them.

These are descriptive counts, not benchmark scores or estimates
of provider-wide quality or availability.

All automatic checks passed despite five semantic nonconformities.
Automatic structure, reference-membership, and status checks did not
establish semantic fidelity.

## Interpretation

The proposed candidate did not demonstrate an advantage under this
known-set, single-sample-per-arm design.

The motivating omission on paraphrase-p2 remained in both arms.
The historical q5 substitution was absent in the fresh baseline,
while the candidate omitted the required contrast altogether.

On q6, the candidate explicitly completed an inference absent from
the fresh baseline, but both arms still failed another required point.

The q5 result is an observed regression under the plan's definition.
One sample per arm does not establish that the instruction caused it,
nor establish a stable difference between the variants.

The candidate was designed after reviewing these cases.
This is not an independent generalization test.

The semantic reviews were performed with the arm identities visible.
They are AI-assisted, not blinded independent assessments.

## Disposition and boundaries

This series provides no basis to promote semantic-fidelity-v1
to Production.

Keep the existing baseline instruction and Production defaults unchanged.
The candidate remains an explicit evaluation-only option.

The authorized 16-invocation sequence is complete.
Do not make additional requests or replace unfavorable samples
as part of this sequence.

Retain all original reports, criteria, and historical assessments.
Do not weaken the rubric to accommodate the returned text.

Any revised instruction, repeated-sample comparison, or unseen-case
evaluation requires a separate plan and network approval.

This review does not record project-author semantic approval,
a validated manual-review storage workflow, or rubric approval.
