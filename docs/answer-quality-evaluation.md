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

## Not implemented in this increment

- Live generation runner.
- Answer report generation and manual verdict storage.
- End-to-end answer-workflow evaluation.
- Corpus snapshot comparison with Aura.
- Model-based judging.

Production generation settings are not changed by these files.
