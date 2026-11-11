# Remaining Roadmap

Status baseline: repository audit at commit `ae3c1e3`.

This roadmap records remaining work. It is not a claim that the listed
capabilities have already been implemented or scientifically approved.

## Working principles

- Preserve the current package layout and working implementation.
- Separate conceptual similarity from historical influence.
- Preserve the distinction between primary passages, bibliographic notes,
  and editorial summaries.
- Separate structural validation from semantic support.
- Keep operator credentials out of publicly served browser code.
- Check free-use constraints before new live provider calls.
- Preserve historical evaluation results; record reassessments separately.

## 1. Core corpus and research scope

Inspect the actual Frank passage records, their sources, text types,
provenance, and rights status.

Define which questions about Cusa, Hegel, and Frank are supported by
the available evidence.

For each proposed historical influence claim, identify supporting sources
and distinguish direct evidence from interpretation or conceptual analogy.

Acceptance criteria:

- Relevant records are classified by evidence type.
- Supported and unsupported research questions are documented.
- Unresolved provenance and rights issues are explicit.
- No influence relationship is added solely because two passages discuss
  related concepts.

## 2. Author review of evaluation criteria

Review the disputed draft criteria and ratings, including p2, q5, and q6
from the controlled answer-instruction experiment.

Acceptance criteria:

- Decisions are recorded with reasons.
- Approved criteria are distinguishable from drafts.
- Historical results remain unchanged.
- Any revised assessment is recorded as a separate review.

Do not begin another prompt experiment before resolving the relevant
criteria.

## 3. One complete user-facing workflow

Complete one bounded scenario:

question
-> retrieval
-> evidence
-> structured answer
-> limitations
-> supporting passages
-> conceptual graph context

Design generation access without exposing the shared operator token
or silently removing the existing protection.

Acceptance criteria:

- The intended user and access model are documented.
- Evidence and source provenance remain inspectable.
- Unsupported questions are handled explicitly.
- Browser and API behavior are covered by appropriate tests.
- Conceptual paths are not labelled as historical influence without evidence.

Add evidence grading, query rewriting, or bounded retries only when a
specific observed failure justifies them. Document their request and
time-budget implications.

## 4. Evaluation coverage

Add German-language questions and evaluate the complete workflow,
not only retrieval or generation from fixed evidence.

Include supported questions, insufficient-evidence questions, and
cross-language retrieval cases.

Acceptance criteria:

- Language and topic coverage are reported explicitly.
- Retrieval quality, answer support, reference validity, and abstention
  behavior are assessed separately.
- Historical checks are distinguished from fresh runs.
- Live calls are performed only after provider and free-use constraints
  have been checked.

## 5. Deployment acceptance and observability

Verify the current application in its intended deployment environment.

Confirm configuration, retrieval readiness, generation access controls,
timeouts, and browser behavior.

Determine and implement only the observability needed to diagnose this
workflow.

Acceptance criteria:

- A fresh deployment acceptance record exists.
- Required configuration and known limitations are documented.
- Tracing is either verified or explicitly marked unavailable.
- Logs and traces do not expose credentials.

## Not required for the nearest version

- Migration to Next.js.
- Reorganisation into a new backend directory structure.
- Universal PDF/EPUB ingestion.
- Automatic extraction of historical influence relationships.
- Additional paid model providers.
- An LLM judge.
- An interactive graph visualisation.
- Terraform or a full monitoring stack.

These items may be reconsidered later if a concrete requirement
justifies them.
