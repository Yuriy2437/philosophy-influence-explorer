"""Run the curated local development seed graph."""

from neo4j import GraphDatabase

from philosophy_influence_explorer.config import get_settings
from philosophy_influence_explorer.graph.seed import seed_demo_graph


def main() -> None:
    """Connect to Neo4j, insert the idempotent seed graph, and close the driver."""
    settings = get_settings()

    with GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(
            settings.neo4j_username,
            settings.neo4j_password.get_secret_value(),
        ),
    ) as driver:
        driver.verify_connectivity(database=settings.neo4j_database)
        seed_demo_graph(driver, settings.neo4j_database)

    print("Demo graph seeded successfully.")


if __name__ == "__main__":
    main()
