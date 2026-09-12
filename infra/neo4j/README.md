# Neo4j development environment

This directory contains local Neo4j infrastructure and graph-schema artifacts for Philosophy Influence Explorer.

## Start Neo4j

From the repository root:

```powershell
docker compose up -d neo4j
docker compose ps
```

Open Neo4j Browser:

```text
http://localhost:7474/browser/
```

Use local credentials from `.env`:

```text
Connect URL: bolt://localhost:7687
Username: value of NEO4J_USERNAME
Password: value of NEO4J_PASSWORD
```

## Apply the graph schema

The script `init/00-schema.cypher` is intentionally idempotent: every statement uses `IF NOT EXISTS`, so it can be run more than once without recreating the same constraints or indexes.

### Option A: Neo4j Browser

### Apply with cypher-shell — recommended

The schema script is mounted read-only inside the Neo4j container at:

```text
/import/init/00-schema.cypher
```

Run the following commands from the repository root in PowerShell.

First, load local environment values into the current PowerShell process:

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $name = $matches.Trim()[4]
        $value = $matches.Trim()[5]
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}
```

Then apply the complete schema in one command:

```powershell
docker compose exec -T neo4j cypher-shell `
  -a bolt://localhost:7687 `
  -u $env:NEO4J_USERNAME `
  -p $env:NEO4J_PASSWORD `
  -d $env:NEO4J_DATABASE `
  --file /import/init/00-schema.cypher
```

The script is idempotent because every schema statement uses `IF NOT EXISTS`. It is therefore safe to run again after restarting the local container.

### Inspect manually in Neo4j Browser

Neo4j Browser remains useful for inspecting results and running individual read-only Cypher queries:

```text
http://localhost:7474/browser/
```

Use the credentials stored in your local `.env`. Do not enter real passwords into Git-tracked files or documentation.

## Verify schema

Run these Cypher queries in Neo4j Browser:

```cypher
SHOW CONSTRAINTS
YIELD name, type, entityType, labelsOrTypes, properties
RETURN name, type, entityType, labelsOrTypes, properties
ORDER BY name;
```

```cypher
SHOW INDEXES
YIELD name, type, entityType, labelsOrTypes, properties, state
RETURN name, type, entityType, labelsOrTypes, properties, state
ORDER BY name;
```

Expected outcome:

- 13 named constraints: 7 node-identity constraints and 6 relationship-identity constraints.
- Range indexes created automatically by uniqueness constraints.
- 6 explicit lookup indexes.
- 3 full-text indexes.
- All indexes eventually reach `ONLINE` state.

## Reset local Neo4j data

Only use this during early development, when no important graph data exists:

```powershell
docker compose down -v
docker compose up -d neo4j
```

The `-v` option deletes named volumes and permanently removes all Neo4j graph data.

## Security

- Never commit `.env`.
- Never place actual passwords or API keys in this directory.
- `.env.example` must contain placeholders only.
- Before committing, run:

```powershell
git status
git diff --cached
```
