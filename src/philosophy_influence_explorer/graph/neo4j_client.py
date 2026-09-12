"""Neo4j driver lifecycle and read-only graph queries."""

from collections.abc import Iterator
from contextlib import contextmanager

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError

from philosophy_influence_explorer.config import Settings


class Neo4jClient:
    """Small application wrapper around the official Neo4j Python driver."""

    def __init__(self, settings: Settings) -> None:
        self._database = settings.neo4j_database
        self._driver: Driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(
                settings.neo4j_username,
                settings.neo4j_password.get_secret_value(),
            ),
        )

    def verify_connectivity(self) -> None:
        """Raise Neo4jError if the database cannot be reached or authenticated."""
        self._driver.verify_connectivity(database=self._database)

    def close(self) -> None:
        """Close the underlying Neo4j driver and its connection pool."""
        self._driver.close()

    @contextmanager
    def session(self) -> Iterator:
        """Yield a Neo4j session bound to the configured database."""
        with self._driver.session(database=self._database) as session:
            yield session

    def get_graph_summary(self) -> dict[str, int]:
        """Return basic node and relationship counts for the graph."""

        query = """
        MATCH (node)
        WITH count(node) AS total_nodes
        MATCH ()-[relationship]->()
        RETURN total_nodes, count(relationship) AS total_relationships
        """

        try:
            with self.session() as session:
                record = session.run(query).single()
        except Neo4jError as error:
            raise RuntimeError("Unable to retrieve graph summary from Neo4j.") from error

        if record is None:
            return {"total_nodes": 0, "total_relationships": 0}

        return {
            "total_nodes": record["total_nodes"],
            "total_relationships": record["total_relationships"],
        }
