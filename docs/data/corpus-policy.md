# Corpus policy

## Scope

The version-controlled corpus is a small research and engineering dataset for a multilingual GraphRAG demonstration. It is not a critical edition, a complete digital library, or a substitute for scholarly source work.

## Rights and redistribution

- The project stores only short quotations tied to identified source records.
- Availability on a website does not by itself mean that text may be redistributed in this Git repository.
- Modern translations are represented as references or project-authored summaries until a specific license permits reuse.
- Every passage must declare `source_id`, `license_status`, `text_kind`, and whether it is verbatim.
- The project currently stores no verbatim passage from Semyon Frank's _Непостижимое_.

## Text provenance

The project distinguishes:

- `primary_quote`: a short verbatim quotation from an identified source;
- `editorial_summary`: a project-authored explanation, not a translation;
- `bibliographic_note`: a project-authored contextual record;
- `translation_reference`: metadata about a translation without reproduction of its text.

An API or UI must not label an editorial summary as a translation.

## Scholarly claims

Direct influence, citation, critical engagement, conceptual affinity, and interpretive hypotheses are different relation types. Every interpretive relation must preserve:

- evidence passage IDs;
- evidence source IDs;
- author of the claim;
- confidence;
- review status;
- timestamps.

Relations with `review_status = candidate` must not be phrased as established historical facts in a user-facing answer.

## Review workflow

1. Add or revise a CSV record.
2. Run `uv run pytest`.
3. Review the cited edition, source location, language, and rights status.
4. Verify that summaries are not represented as translations.
5. Apply the corpus locally and inspect resulting graph paths.
6. Commit the data and its provenance together.
