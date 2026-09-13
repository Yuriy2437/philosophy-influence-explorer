# Curation guide

## Purpose

This guide explains how to extend the starter corpus without weakening source provenance, multilingual clarity, or the scholarly distinction between historical fact and interpretation.

## Adding a source

Add one row to `data/curated/sources.csv` before adding a passage from that source.

Required source metadata:

- stable `id` beginning with `source:`;
- `citation_key`;
- title, author/editor, and publication year where known;
- source type;
- canonical URL if available;
- explicit `license_status`;
- a practical access and rights note;
- `review_status`.

Do not use `public_domain` as a guess. Record the precise claim shown by the source, for example `public_domain_us`, `public_domain_mark_1_0`, `open_license`, `rights_to_verify`, or `reference_only`.

## Adding a passage

Add one row to `data/curated/passages.csv`.

Rules:

- Save the CSV in UTF-8.
- Use a stable ID beginning with `passage:`.
- Reference existing `work_id` and `source_id`.
- Use `primary_quote` only for a short verbatim passage from an identified source.
- Mark a verbatim passage with `is_verbatim=true` and `is_editorial=false`.
- Use `editorial_summary` for an original project explanation, with `is_verbatim=false` and `is_editorial=true`.
- Do not call an editorial summary a translation.
- Provide a stable location in `position_label` and a human-readable `citation_label`.
- Use the original language code where possible: `la`, `de`, `ru`, or `en`.

## Adding a relation

Add one row to `data/curated/relations.csv`.

- Use only a relation type currently allowed by `RelationType`.
- `from_id` and `to_id` must already exist in the corpus.
- Encode relation properties as valid JSON in `properties_json`.
- Escape quotes inside CSV JSON as doubled quotes.
- For `CONCEPTUALLY_RELATED_TO`, include full provenance: relation subtype, evidence passage/source IDs, claim language, confidence, author, review status, and timestamps.
- Do not use `DIRECTLY_INFLUENCED` until the project has a documented evidence policy and supporting source material.

## Validate and ingest

From the repository root:

```powershell
uv run pytest
docker compose up -d neo4j
uv run python scripts/seed_curated_corpus.py
```

Inspect the result in Neo4j Browser at:

```text
http://localhost:7474/browser/
```

## Example editorial distinction

Correct:

```text
text_kind: editorial_summary
is_verbatim: false
is_editorial: true
citation_label: Editorial summary of De docta ignorantia I.4
```

Incorrect:

```text
text_kind: primary_quote
is_verbatim: true
is_editorial: false
text: [a project-authored paraphrase]
```
