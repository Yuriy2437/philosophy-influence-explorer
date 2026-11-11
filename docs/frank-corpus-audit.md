# Frank Corpus Audit

Audit date: 2026-11-11.

Repository baseline: `ceb6545`.

Scope: inspection of the supplied curated records and implementation.
No external edition, rights verification, live retrieval run, or generation
request was performed as part of this audit.

## Corpus findings

The inspected corpus contains three Frank passage records:

| Passage suffix | Material type              | Source                     |
| -------------- | -------------------------- | -------------------------- |
| `meta:ru`      | Project bibliographic note | Frank bibliographic record |
| `summary:en`   | Project editorial summary  | Project editorial source   |
| `summary:de`   | Project editorial summary  | Project editorial source   |

All three records have `is_verbatim=false` and `is_editorial=true`.

No verbatim Frank passage is included in the inspected corpus.

The three language records must not be treated as three independent
scholarly witnesses. They express a shared project-level characterization.

The work's `primary_text` classification describes the work, not the
evidence type of every associated passage.

## Source and rights limitations

The Frank bibliographic source has no URL and explicitly states that
no verbatim text is included pending an audit of a specific source
and its licence.

Its rights status remains `rights_to_verify`.

The editorial source identifies its records as project-authored materials,
not published translations.

Review status does not resolve source or rights verification.

## Retrieval and evidence handling

Semantic retrieval supports `is_verbatim` and `is_editorial` filters.

With `is_verbatim=true` and `is_editorial=false`, the inspected Frank
records are excluded from semantic results.

Graph expansion also supports these filters for related passages.
It does not re-filter caller-supplied seeds. This audit does not separately
verify filter forwarding by the composing service.

Graph expansion traverses only `reviewed` or `curated` DISCUSSES edges.
This is edge acceptance, not approval of the retrieved passage's content.

Evidence preparation deduplicates by passage ID and rejects conflicting
records for an identical ID. It does not identify independent witnesses
or assess answer sufficiency.

## Information supplied to generation

The generation payload includes passage text and these provenance fields:

- source and work IDs;
- citation label;
- language and text kind;
- review status;
- verbatim, editorial, and machine-generated flags.

It does not include full source records, source URLs, source access notes,
licensing fields, translation references, or a separate position label.

The current system instruction distinguishes editorial summaries from
primary quotations and translations, prohibits unsupported additions,
and warns against inferring influence or independent corroboration from
shared concepts.

These instructions are not an independent semantic verification mechanism.
Structure and reference validation do not establish claim support.

## Derivation metadata ambiguity

The editorial summaries reference the Russian note through
`translation_of_passage_id`.

Ingestion deliberately creates a `TRANSLATION_OF` edge with
`status=editorial_summary_of` for editorial summaries.

This preserves a derivation link but overloads translation terminology.

No CSV references or graph relationships were changed in this audit.
A future model decision should distinguish translation from editorial
derivation and account for existing ingestion and stored relationships.

## Current research boundary

The records may be presented as project notes about Frank, with their
editorial character disclosed.

They do not provide primary-text support for:

- detailed reconstruction of arguments in The Unknowable;
- comparisons of specific formulations across Frank, Cusa, and Hegel;
- quotations or published translations of Frank;
- a documented historical influence chain.

## Next bounded task

Select one concrete research question and a specific source edition.

Before adding a passage:

1. Record the edition and a stable locator.
2. Check the relevant source and reuse constraints.
3. Verify the proposed transcription against that source.
4. Classify quotation, translation, and editorial explanation separately.
5. State what the passage supports and what remains unsupported.

Do not add influence edges merely because passages discuss related concepts.

## Changes made

None to corpus data, application code, prompts, database contents,
or historical evaluation results.
