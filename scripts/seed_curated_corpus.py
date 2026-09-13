"""Validate and ingest the version-controlled curated corpus into Neo4j."""

from pathlib import Path

from neo4j import GraphDatabase

from philosophy_influence_explorer.config import get_settings
from philosophy_influence_explorer.ingestion.curated_seed import seed_curated_corpus


def main() -> None:
    """Connect to Neo4j, validate CSV data, and load the curated corpus."""
    project_root = Path(__file__).resolve().parents[1]
    corpus_dir = project_root / "data" / "curated"
    settings = get_settings()

    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(
            settings.neo4j_username,
            settings.neo4j_password.get_secret_value(),
        ),
    ) as driver:
        driver.verify_connectivity(database=settings.neo4j_database)
        counts = seed_curated_corpus(
            driver=driver,
            database=settings.neo4j_database,
            corpus_dir=corpus_dir,
        )

    summary = ", ".join(f"{name}={count}" for name, count in counts.items())
    print(f"Curated corpus seeded successfully: {summary}")


if __name__ == "__main__":
    main()
