# Graph data model

## Purpose

Philosophy Influence Explorer represents a multilingual philosophical corpus as a source-grounded knowledge graph. The graph supports three related tasks:

1. Retrieval of passages relevant to a user question.
2. Navigation through explicit conceptual and intellectual relations.
3. Generation of answers whose claims can be traced to source evidence.

The model is designed to distinguish documented historical influence from conceptual similarity and from unverified interpretive hypotheses.

## Design principles

- Every core entity has a stable, application-generated identifier.
- Raw textual evidence is represented as `Passage` nodes rather than being reduced to metadata.
- A relation representing a scholarly claim must preserve provenance and review status.
- The primary text language, translation status, and text version must remain visible.
- LLM extraction can create candidate data, but only curated/reviewed claims may be presented as verified historical facts.
- Retrieval and generation must be able to return “insufficient evidence in the current corpus”.

## Node labels

| Label         | Meaning                                                 | Required identity property | Selected properties                                                                                                 |
| ------------- | ------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `Philosopher` | Historical author, thinker, commentator, or interpreter | `id`                       | `canonical_name`, `name_en`, `name_ru`, `name_de`, `birth_year`, `death_year`, `bio_note`                           |
| `Work`        | A distinct work, edition, translation, or corpus unit   | `id`                       | `title`, `title_en`, `title_ru`, `title_de`, `original_language`, `publication_year`, `work_kind`, `is_translation` |
| `Passage`     | A citable text fragment used for retrieval and evidence | `id`                       | `text`, `text_normalized`, `language`, `work_id`, `position_label`, `section_order`, `token_count`                  |
| `Concept`     | A controlled philosophical concept                      | `id`                       | `canonical_label`, `label_en`, `label_ru`, `label_de`, `description`, `concept_family`                              |
| `Source`      | A bibliographic, editorial, or digital source record    | `id`                       | `citation_key`, `title`, `authors`, `publication_year`, `source_type`, `license_status`, `url`                      |
| `Language`    | A language represented by a stable language code        | `code`                     | `name_en`, `name_ru`, `name_de`                                                                                     |
| `Period`      | Intellectual, historical, or philosophical period       | `id`                       | `label`, `start_year`, `end_year`, `description`                                                                    |

## Structural relationships

| Type              | Direction                                    | Meaning                                   | Important properties                               |
| ----------------- | -------------------------------------------- | ----------------------------------------- | -------------------------------------------------- | -------- |
| `WROTE`           | `(Philosopher)-[:WROTE]->(Work)`             | Authorship                                | `role`, `certainty`                                |
| `HAS_PASSAGE`     | `(Work)-[:HAS_PASSAGE]->(Passage)`           | Work contains a citable passage           | `order`                                            |
| `IN_LANGUAGE`     | `(Work                                       | Passage)-[:IN_LANGUAGE]->(Language)`      | Language of a text object                          | `status` |
| `TRANSLATION_OF`  | `(Work)-[:TRANSLATION_OF]->(Work)`           | Translation or edition relationship       | `translator`, `translation_year`, `status`         |
| `DISCUSSES`       | `(Passage)-[:DISCUSSES]->(Concept)`          | Passage discusses a controlled concept    | `extraction_method`, `confidence`, `review_status` |
| `PUBLISHED_IN`    | `(Work)-[:PUBLISHED_IN]->(Period)`           | Work belongs to/was published in a period | `certainty`                                        |
| `ASSOCIATED_WITH` | `(Philosopher)-[:ASSOCIATED_WITH]->(Period)` | Interpretive period association           | `source_id`, `review_status`                       |

## Scholarly-claim relationships

The following relationships encode claims that require provenance. All must have a stable relationship `id`.

| Type                      | Direction     | Meaning                      | Required evidence properties                      |
| ------------------------- | ------------- | ---------------------------- | ------------------------------------------------- | --------- | ------------------------------ | ----------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `CITES`                   | `(Passage     | Philosopher)-[:CITES]->(Work | Philosopher                                       | Passage)` | Explicit citation or reference | `id`, `evidence_passage_ids`, `review_status`                           |
| `DIRECTLY_INFLUENCED`     | `(Philosopher | Work                         | Concept)-[:DIRECTLY_INFLUENCED]->(Philosopher     | Work      | Concept)`                      | Evidence-supported historical influence                                 | `id`, `evidence_source_ids`, `asserted_by`, `confidence`, `review_status`   |
| `CRITICALLY_ENGAGES_WITH` | `(Philosopher | Work                         | Passage)-[:CRITICALLY_ENGAGES_WITH]->(Philosopher | Work      | Concept)`                      | Explicit critique, analysis, or engagement                              | `id`, `evidence_passage_ids`, `review_status`                               |
| `CONCEPTUALLY_RELATED_TO` | `(Concept     | Passage                      | Philosopher)-[:CONCEPTUALLY_RELATED_TO]->(Concept | Passage   | Philosopher)`                  | Thematic or conceptual affinity, not automatically historical influence | `id`, `relation_type`, `evidence_source_ids`, `confidence`, `review_status` |
| `INTERPRETS`              | `(Philosopher | Work                         | Passage)-[:INTERPRETS]->(Philosopher              | Work      | Concept)`                      | Interpretive relation, often secondary literature                       | `id`, `evidence_source_ids`, `asserted_by`, `review_status`                 |
| `TRANSMITTED_THROUGH`     | `(Concept     | Work                         | Philosopher)-[:TRANSMITTED_THROUGH]->(Philosopher | Work      | Concept)`                      | Mediated reception/transmission path                                    | `id`, `evidence_source_ids`, `review_status`                                |

## Mandatory provenance fields

Every scholarly-claim relationship should use the following property contract:

```text
id: stable UUID or application-generated identifier
relation_type: controlled subtype, especially for CONCEPTUALLY_RELATED_TO
asserted_by: "curator" | "llm_candidate" | "secondary_source"
evidence_passage_ids: list of Passage IDs
evidence_source_ids: list of Source IDs
claim_language: BCP 47 language tag, for example "ru", "en", "de", or "la"
confidence: number from 0.0 to 1.0
review_status: "curated" | "reviewed" | "candidate" | "rejected"
created_at: ISO 8601 timestamp
updated_at: ISO 8601 timestamp
```

A relationship with `review_status = "candidate"` may be available to a human curator in a review UI, but it must not be expressed to users as established historical fact.

## Example: provenance-aware conceptual relation

```cypher
MATCH (cusa:Philosopher {id: "philosopher:cusanus"})
MATCH (hegel:Philosopher {id: "philosopher:hegel"})
CREATE (cusa)-[:CONCEPTUALLY_RELATED_TO {
  id: "relation:conceptual-affinity:cusanus-hegel:001",
  relation_type: "dialectical_coincidence_of_opposites",
  asserted_by: "curator",
  evidence_passage_ids: [
    "passage:cusanus:de-docta-ignorantia:1.4",
    "passage:hegel:science-of-logic:being-nothing"
  ],
  evidence_source_ids: [
    "source:curated-bibliography:001"
  ],
  claim_language: "en",
  confidence: 0.85,
  review_status: "reviewed",
  created_at: "2026-09-10T00:00:00Z",
  updated_at: "2026-09-10T00:00:00Z"
}]->(hegel);
```

This example does not state a direct historical influence. It records a reviewed conceptual affinity, identifies its subtype, and links the claim to evidence.

## Retrieval implications

The graph supports three retrieval modes:

- **Lexical retrieval:** Neo4j full-text indexes find terminology, names, and exact phrases in Russian, English, and German.
- **Graph retrieval:** Cypher traversals find concepts, passages, works, and philosophers connected by explicit relationships.
- **Vector retrieval:** a future Neo4j vector index will retrieve semantically similar passages after a multilingual embedding model is selected.

A final GraphRAG answer should combine retrieved passages with graph paths, cite the supporting text, and distinguish evidence-backed findings from tentative interpretive relationships.

## Initial scope

The first curated corpus will include:

- Nicholas of Cusa;
- Georg Wilhelm Friedrich Hegel;
- Semyon Frank.

The schema is deliberately broader than the initial corpus so that Schelling, Husserl, Heidegger, translations, and secondary literature can be introduced without a breaking data-model migration.
