// =============================================================================
// Philosophy Influence Explorer — Neo4j Graph Schema
// =============================================================================
// Purpose:
//   Define identity constraints and retrieval indexes for the multilingual,
//   source-grounded philosophical knowledge graph.
//
// Design principles:
//   - Stable, application-generated IDs are used for identity.
//   - Relations involving intellectual influence require provenance properties.
//   - Text retrieval will use full-text indexes; vector indexes come later,
//     when an embedding model and embedding dimension are selected.
//   - Statements are idempotent: rerunning the script is safe.
// =============================================================================


// -----------------------------------------------------------------------------
// 1. Uniqueness constraints for core node identities
// -----------------------------------------------------------------------------

CREATE CONSTRAINT philosopher_id_unique IF NOT EXISTS
FOR (node:Philosopher)
REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT work_id_unique IF NOT EXISTS
FOR (node:Work)
REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
FOR (node:Concept)
REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT passage_id_unique IF NOT EXISTS
FOR (node:Passage)
REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT source_id_unique IF NOT EXISTS
FOR (node:Source)
REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT period_id_unique IF NOT EXISTS
FOR (node:Period)
REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT language_code_unique IF NOT EXISTS
FOR (node:Language)
REQUIRE node.code IS UNIQUE;


// -----------------------------------------------------------------------------
// 2. Lookup indexes for common filters and navigational queries
// -----------------------------------------------------------------------------

CREATE INDEX philosopher_canonical_name IF NOT EXISTS
FOR (node:Philosopher)
ON (node.canonical_name);

CREATE INDEX work_title IF NOT EXISTS
FOR (node:Work)
ON (node.title);

CREATE INDEX concept_canonical_label IF NOT EXISTS
FOR (node:Concept)
ON (node.canonical_label);

CREATE INDEX passage_work_id IF NOT EXISTS
FOR (node:Passage)
ON (node.work_id);

CREATE INDEX passage_language IF NOT EXISTS
FOR (node:Passage)
ON (node.language);

CREATE INDEX source_citation_key IF NOT EXISTS
FOR (node:Source)
ON (node.citation_key);


// -----------------------------------------------------------------------------
// 3. Full-text indexes for lexical search in multilingual texts
// -----------------------------------------------------------------------------
// These indexes support exact terminology, names, and phrase searches.
// Semantic/vector retrieval will be added later after embeddings are selected.

CREATE FULLTEXT INDEX work_fulltext IF NOT EXISTS
FOR (node:Work)
ON EACH [node.title, node.title_en, node.title_ru, node.title_de];

CREATE FULLTEXT INDEX passage_fulltext IF NOT EXISTS
FOR (node:Passage)
ON EACH [node.text, node.text_normalized];

CREATE FULLTEXT INDEX concept_fulltext IF NOT EXISTS
FOR (node:Concept)
ON EACH [
  node.canonical_label,
  node.label_en,
  node.label_ru,
  node.label_de,
  node.description
];


// -----------------------------------------------------------------------------
// 4. Provenance-aware relationship identity constraints
// -----------------------------------------------------------------------------
// Each relationship that represents a scholarly claim must receive a stable ID.
// This prevents accidental duplicate claims during ingestion and supports
// review/audit workflows later.

CREATE CONSTRAINT cites_id_unique IF NOT EXISTS
FOR ()-[relation:CITES]-()
REQUIRE relation.id IS UNIQUE;

CREATE CONSTRAINT direct_influence_id_unique IF NOT EXISTS
FOR ()-[relation:DIRECTLY_INFLUENCED]-()
REQUIRE relation.id IS UNIQUE;

CREATE CONSTRAINT critical_engagement_id_unique IF NOT EXISTS
FOR ()-[relation:CRITICALLY_ENGAGES_WITH]-()
REQUIRE relation.id IS UNIQUE;

CREATE CONSTRAINT conceptual_relation_id_unique IF NOT EXISTS
FOR ()-[relation:CONCEPTUALLY_RELATED_TO]-()
REQUIRE relation.id IS UNIQUE;

CREATE CONSTRAINT interpretation_id_unique IF NOT EXISTS
FOR ()-[relation:INTERPRETS]-()
REQUIRE relation.id IS UNIQUE;

CREATE CONSTRAINT transmission_id_unique IF NOT EXISTS
FOR ()-[relation:TRANSMITTED_THROUGH]-()
REQUIRE relation.id IS UNIQUE;
