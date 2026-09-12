"""Curated, provenance-aware MVP seed graph for local development."""

from neo4j import Driver

SEED_QUERY = """
MERGE (cusanus:Philosopher {id: "philosopher:cusanus"})
SET cusanus.canonical_name = "Nicholas of Cusa",
    cusanus.name_en = "Nicholas of Cusa",
    cusanus.name_ru = "Николай Кузанский",
    cusanus.name_de = "Nikolaus von Kues",
    cusanus.birth_year = 1401,
    cusanus.death_year = 1464,
    cusanus.bio_note = "Cardinal, philosopher, theologian, and early Renaissance thinker."

MERGE (hegel:Philosopher {id: "philosopher:hegel"})
SET hegel.canonical_name = "Georg Wilhelm Friedrich Hegel",
    hegel.name_en = "Georg Wilhelm Friedrich Hegel",
    hegel.name_ru = "Георг Вильгельм Фридрих Гегель",
    hegel.name_de = "Georg Wilhelm Friedrich Hegel",
    hegel.birth_year = 1770,
    hegel.death_year = 1831,
    hegel.bio_note = "German idealist philosopher."

MERGE (frank:Philosopher {id: "philosopher:frank"})
SET frank.canonical_name = "Semyon Frank",
    frank.name_en = "Semyon Frank",
    frank.name_ru = "Семён Франк",
    frank.name_de = "Semjon Frank",
    frank.birth_year = 1877,
    frank.death_year = 1950,
    frank.bio_note = "Russian religious philosopher."

MERGE (docta_ignorantia:Concept {id: "concept:docta-ignorantia"})
SET docta_ignorantia.canonical_label = "docta ignorantia",
    docta_ignorantia.label_en = "learned ignorance",
    docta_ignorantia.label_ru = "учёное незнание",
    docta_ignorantia.label_de = "gelehrte Unwissenheit",
    docta_ignorantia.description = "Cusan: awareness of finite intellect before infinity."

MERGE (coincidentia_oppositorum:Concept {id: "concept:coincidentia-oppositorum"})
SET coincidentia_oppositorum.canonical_label = "coincidentia oppositorum",
    coincidentia_oppositorum.label_en = "coincidence of opposites",
    coincidentia_oppositorum.label_ru = "совпадение противоположностей",
    coincidentia_oppositorum.label_de = "Zusammenfall der Gegensätze",
    coincidentia_oppositorum.description = "Cusan: unity of opposites in the absolute."

MERGE (absolute:Concept {id: "concept:absolute"})
SET absolute.canonical_label = "absolute",
    absolute.label_en = "absolute",
    absolute.label_ru = "абсолют",
    absolute.label_de = "das Absolute",
    absolute.description = "Cross-tradition concept; meaning varies by philosopher."

MERGE (cusanus_work:Work {id: "work:cusanus:de-docta-ignorantia"})
SET cusanus_work.title = "De docta ignorantia",
    cusanus_work.title_en = "On Learned Ignorance",
    cusanus_work.title_ru = "Об учёном незнании",
    cusanus_work.title_de = "De docta ignorantia",
    cusanus_work.original_language = "la",
    cusanus_work.publication_year = 1440,
    cusanus_work.work_kind = "primary_text",
    cusanus_work.is_translation = false

MERGE (hegel_work:Work {id: "work:hegel:science-of-logic"})
SET hegel_work.title = "Wissenschaft der Logik",
    hegel_work.title_en = "Science of Logic",
    hegel_work.title_ru = "Наука логики",
    hegel_work.title_de = "Wissenschaft der Logik",
    hegel_work.original_language = "de",
    hegel_work.publication_year = 1812,
    hegel_work.work_kind = "primary_text",
    hegel_work.is_translation = false

MERGE (frank_work:Work {id: "work:frank:unknowable"})
SET frank_work.title = "Непостижимое",
    frank_work.title_en = "The Unknowable",
    frank_work.title_ru = "Непостижимое",
    frank_work.title_de = "Das Unergründliche",
    frank_work.original_language = "ru",
    frank_work.publication_year = 1939,
    frank_work.work_kind = "primary_text",
    frank_work.is_translation = false

MERGE (cusanus)-[:WROTE {role: "author", certainty: 1.0}]->(cusanus_work)
MERGE (hegel)-[:WROTE {role: "author", certainty: 1.0}]->(hegel_work)
MERGE (frank)-[:WROTE {role: "author", certainty: 1.0}]->(frank_work)

MERGE (cusanus_work)-[:DISCUSSES {
    extraction_method: "curated",
    confidence: 1.0,
    review_status: "curated"
}]->(docta_ignorantia)

MERGE (cusanus_work)-[:DISCUSSES {
    extraction_method: "curated",
    confidence: 1.0,
    review_status: "curated"
}]->(coincidentia_oppositorum)

MERGE (cusanus_work)-[:DISCUSSES {
    extraction_method: "curated",
    confidence: 0.9,
    review_status: "curated"
}]->(absolute)

MERGE (hegel_work)-[:DISCUSSES {
    extraction_method: "curated",
    confidence: 0.9,
    review_status: "reviewed"
}]->(absolute)

MERGE (frank_work)-[:DISCUSSES {
    extraction_method: "curated",
    confidence: 0.9,
    review_status: "reviewed"
}]->(absolute)

MERGE (docta_ignorantia)-[:CONCEPTUALLY_RELATED_TO {
    id: "relation:conceptual:docta-ignorantia:absolute:001",
    relation_type: "epistemic_limit_and_absolute",
    asserted_by: "curator",
    evidence_passage_ids: [],
    evidence_source_ids: [],
    claim_language: "en",
    confidence: 0.6,
    review_status: "candidate",
    created_at: "2026-09-12T00:00:00Z",
    updated_at: "2026-09-12T00:00:00Z"
}]->(absolute)

MERGE (coincidentia_oppositorum)-[:CONCEPTUALLY_RELATED_TO {
    id: "relation:conceptual:coincidentia-oppositorum:absolute:001",
    relation_type: "unity_of_opposites_in_the_absolute",
    asserted_by: "curator",
    evidence_passage_ids: [],
    evidence_source_ids: [],
    claim_language: "en",
    confidence: 0.7,
    review_status: "candidate",
    created_at: "2026-09-12T00:00:00Z",
    updated_at: "2026-09-12T00:00:00Z"
}]->(absolute)
"""


def seed_demo_graph(driver: Driver, database: str) -> None:
    """Create or update the minimal curated graph used during local development."""
    driver.execute_query(
        SEED_QUERY,
        database_=database,
    )
