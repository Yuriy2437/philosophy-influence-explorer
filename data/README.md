# Curated corpus data

This directory contains the small, version-controlled starter corpus for Philosophy Influence Explorer.

The corpus is deliberately small. It exists to validate the data model, source provenance, multilingual metadata, ingestion workflow, and future GraphRAG retrieval. It is not a complete scholarly edition or a replacement for critical editions.

## Directory layout

```text
curated/
  philosophers.csv  # Controlled philosopher records
  works.csv         # Works, editions, and corpus units
  concepts.csv      # Controlled concept vocabulary
  sources.csv       # Bibliographic and rights/provenance records
  passages.csv      # Citable passages, summaries, and notes
  relations.csv     # Curated graph relationships

schemas/
  passage.schema.json
  relation.schema.json
```

## Text kinds

| `text_kind`             | Meaning                                                  | `is_verbatim` |
| ----------------------- | -------------------------------------------------------- | ------------: |
| `primary_quote`         | Short quotation from an identified source                |        `true` |
| `editorial_summary`     | Original explanatory summary written for this project    |       `false` |
| `bibliographic_note`    | Project-authored bibliographic or contextual note        |       `false` |
| `translation_reference` | Metadata describing a translation without reproducing it |       `false` |

An `editorial_summary` is not a published translation, and must never be presented as one in the API or UI.

## Rights policy

- Only short quotations from identified source records may be stored as `primary_quote`.
- Modern translations are not copied into this repository unless their licence explicitly permits redistribution.
- Online availability does not by itself establish a redistribution right.
- Each passage must reference a `source_id` and a `license_status`.
- The corpus does not currently include verbatim text from Semyon Frank's _Непостижимое_.

## Editorial review

The corpus is prepared as a technical starter pack and requires scholarly review before release. Each record has `review_status`:

- `curated`: supplied and checked by the project curator;
- `reviewed`: reviewed by a domain expert;
- `candidate`: proposed data not yet approved;
- `rejected`: excluded from user-facing retrieval.

## Stable identifiers

Identifiers are stable and application-generated. Examples:

```text
philosopher:cusanus
work:cusanus:de-docta-ignorantia
concept:docta-ignorantia
source:hegel:gutenberg-6729
passage:cusanus:ddi:1.4:la
relation:passage:cusanus-ddi-1-4:discusses:coincidentia-oppositorum
```
