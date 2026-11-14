# Project-author review: answer-quality-v1 experiment

Review date: 2026-11-13.

## Scope and authority

This document records explicit decisions approved by the project author
during an AI-assisted review of all eight cases and all 16 returned
answers from the completed semantic-fidelity-v1 fixed-evidence
instruction experiment.

The p2, q5, and q6 decisions were approved first. The remaining five
cases were approved subsequently on the same date.

The review used:

- the case criteria from data/evaluation/answer-quality-v1.json;
- the corresponding passage text supplied from the curated CSV corpus;
- the baseline and candidate answer text reproduced in the experiment review.

Related documents:

- [Experiment review](answer-quality-prompt-experiment-review.md)
- [Evaluation conventions](answer-quality-evaluation.md)

This is project-author approval of the case requirements for the current
eight-case answer-quality-v1 suite and the assessments of the 16 specified
experiment answers.

It is not an independent scholarly assessment, a new provider run,
approval of every historical answer, or validation of future answers.

It does not independently verify quotations, editions, translations,
or source-rights status.

## answer-paraphrase-p2

Author approval date: 2026-11-13.

### Criterion decision

Retain the existing required limitation.

The only-permissible-purpose formulation does not establish that any
risk to others or any proposed coercive measure is sufficient to justify
coercion within the passage's stated scope.

This requirement asks the answer to state the boundary explicitly.
It does not imply that every answer omitting it makes a false assertion.

### Answer decisions

Both baseline and semantic-fidelity-v1 fail to satisfy the required
limitation.

The reason is omission of an explicit boundary, not an assertion that
any risk automatically justifies any coercive measure. Neither answer
makes that assertion.

The baseline rejects the person's own good as sufficient justification
more directly. The candidate conveys that exclusion indirectly through
the only-purpose formulation.

Neither arm meets the existing case criteria.

## answer-q5

Author approval date: 2026-11-13.

### Criterion decision

Retain the requirement to distinguish this determinate unity of being
and nothing from a unity that abstracts from being and nothing.

The contrast is explicitly present in the supplied passage and clarifies
the relation asked about.

### Answer decisions

The baseline meets the case criteria with wording caveats.

"Undividedeness" is awkward English. The phrase "rather than an
abstraction from them" compresses the source construction but preserves
the required contrast sufficiently.

The candidate does not meet the case criteria because it omits the
required contrast. This is an omission, not an explicit denial of
that contrast.

The candidate also answers in German despite an English question.
Record this separately as an instruction-language violation.

The baseline-to-candidate difference remains an observed semantic
regression for this pair under the experiment's definition.
It does not establish that the instruction caused the difference.

## answer-q6

Author approval date: 2026-11-13.

### Criterion decision

Retain both existing required points:

- the easy-versus-difficult contrast in the supplied passage;
- the connection between escaping every proportion and
  incomprehensibility in this context.

### Answer decisions

Both answers fail the first required point.

They replace the characterization of inquiry as easy within comparative
proportional relations with the stronger statement that all inquiry
relies on those relations.

This is a semantic substitution as well as a loss of the explicit
easy-versus-difficult contrast.

The candidate states the inference to incomprehensibility explicitly
and is more complete on the second required point.

The baseline contains the premise but does not explicitly state the
conclusion. Because the question already asks about comprehension,
this lack of explicitness is not treated as the sole basis for failure.

Neither arm meets the existing case criteria.
No baseline-to-candidate semantic regression is recorded for this pair.

This decision does not assert that a broader account of proportional
inquiry is absent from Cusa's other writing. The assessment is limited
to fidelity to the supplied excerpt.

The different historical answer from the earlier series is not reassessed.

## answer-q1

Author approval date: 2026-11-13.

### Criterion decision

Approve the existing status-dependent requirements.

For partial status, the answer must accurately state the humanity-as-end
principle, preserve never merely as a means, and explicitly identify
the missing justification.

For insufficient_evidence status, the answer must explain the missing
justification without claims.

A restatement of the imperative is not a complete explanation of why
it holds. Unsupported arguments from dignity, rational nature, autonomy,
or intrinsic worth must not be added.

The empty required_points list does not remove the conditional semantic
requirements expressed in the rationale and evaluation conventions.

### Answer decisions

Both experiment answers have partial status and meet the requirements.

They preserve the qualification concerning merely being used as a means,
identify the missing justification, and do not supply unsupported
arguments.

## answer-paraphrase-p1

Author approval date: 2026-11-13.

### Criterion decision

Approve the existing requirements.

The question asks how to act, rather than why the principle holds.
The answer must preserve treating humanity in another person as an end
and never merely as a means.

An accurate rendering of merely or only can preserve this distinction
without a separate mandatory explanation about permissible assistance.

Generated Russian wording must not be presented as a published or
independently verified translation.

### Answer decisions

Both experiment answers meet the requirements.

Both preserve the qualification only and do not prohibit every
instrumental aspect of interaction.

The candidate's additional reference to one's own person is consistent
with the supplied formulation and does not prevent it from answering
the question about another person.

## answer-q2

Author approval date: 2026-11-13.

### Criterion decision

Approve both existing required points:

- autonomy as the property by which the will is a law to itself,
  independently of properties of the objects of volition;
- the connection between choosing, maxims of choice, and universal law.

Do not equate autonomy with arbitrary preference or add an unsupported
broader derivation.

### Answer decisions

The baseline meets the requirements.

The candidate meets the requirements with a wording caveat:
"the property of the autonomy of the will" is awkward and less precise
than identifying autonomy as a property of the will.

The remainder of the candidate answer preserves the required definition
and principle sufficiently. The caveat is not treated as failure of
a required point in this answer.

## answer-negative-n1

Author approval date: 2026-11-13.

### Criterion decision

Approve the existing requirements.

Thematically related passages about the practical imperative and autonomy
do not supply the requested definition and comparison of hypothetical
and categorical imperatives.

Require insufficient_evidence with no claims and a specific explanation
of the missing comparison.

### Answer decisions

Both experiment answers meet the requirements.

Both identify the missing comparison, contain no claims, and limit
their conclusion to the supplied excerpts.

The baseline's statement that the excerpts contain no information
about how the distinction is made is understood as identifying the
missing comparison, not denying all thematic relevance.

## answer-negative-n3

Author approval date: 2026-11-13.

### Criterion decision

Approve the existing requirements.

Require insufficient_evidence with no claims because the supplied
philosophical passages do not describe the requested experimental
evidence.

Do not answer from background physics knowledge, treat philosophical
concepts as experimental evidence, or infer that relevant experiments
do not exist elsewhere.

### Answer decisions

Both experiment answers meet the requirements.

The candidate's longer description of the supplied material is acceptable
but does not establish an advantage over the concise baseline.

Passage IDs mentioned freely in limitations are not structured claim
references. Their presence must not be represented as automatic
validation of those mentions.

## Approved experiment summary

The project author approved the requirements for all eight cases and
the assessments of all 16 returned answers from the specified experiment.

| Outcome                                            | Baseline | Candidate |
| -------------------------------------------------- | -------: | --------: |
| Meets case requirements, including wording caveats |        6 |         5 |
| Does not meet case requirements                    |        2 |         3 |

Wording caveats apply to baseline q5 and candidate q2.

These are descriptive counts for this known-set experiment, not
benchmark estimates or evidence of a causal instruction effect.

The earlier historical series is not reassessed by this approval.

## Preservation and disposition

No new generation, retrieval, or graph-expansion run was performed
for this review.

Original JSON reports remain unchanged.
Their manual_review fields remain null.

The historical AI-assisted experiment review remains unchanged.
This document records subsequent project-author decisions separately.

The case dataset, Production instruction, and generation defaults
are unchanged.

These decisions approve the case requirements of the current eight-case
suite, as interpreted in this review, and the assessments of the
16 specified experiment answers.

They do not independently verify source texts, validate the evaluation
software, approve the earlier historical answers, or establish
generalization to future cases.

The separate author-review record does not populate or validate
the JSON manual_review workflow.

The decisions do not provide a basis to promote semantic-fidelity-v1
to Production.
