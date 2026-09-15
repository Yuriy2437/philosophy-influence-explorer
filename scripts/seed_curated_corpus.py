"""Validate and seed the version-controlled curated corpus into Neo4j."""

from __future__ import annotations

import argparse
from pathlib import Path

from neo4j import GraphDatabase

from philosophy_influence_explorer.config import Settings
from philosophy_influence_explorer.ingestion.curated_seed import (
    reset_curated_corpus,
    seed_curated_corpus,
)

settings = Settings()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = PROJECT_ROOT / "data" / "curated"


def parse_args() -> argparse.Namespace:
    """Parse command-line options for curated corpus seeding."""
    parser = argparse.ArgumentParser(
        description="Validate and seed the curated corpus into Neo4j."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete only graph records owned by curated_corpus_v1 before seeding.",
    )
    return parser.parse_args()


def main() -> None:
    """Optionally reset, then validate and seed the curated corpus."""
    args = parse_args()

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(
            settings.neo4j_username,
            settings.neo4j_password.get_secret_value(),
        ),
    )

    try:
        driver.verify_connectivity()

        if args.reset:
            reset_curated_corpus(
                driver=driver,
                database=settings.neo4j_database,
            )

        counts = seed_curated_corpus(
            driver=driver,
            database=settings.neo4j_database,
            corpus_dir=CORPUS_DIR,
        )
    finally:
        driver.close()

    print(
        "Curated corpus seeded successfully: "
        f"philosophers={counts['philosophers']}, "
        f"works={counts['works']}, "
        f"concepts={counts['concepts']}, "
        f"sources={counts['sources']}, "
        f"passages={counts['passages']}, "
        f"relations={counts['relations']}"
    )


if __name__ == "__main__":
    main()
