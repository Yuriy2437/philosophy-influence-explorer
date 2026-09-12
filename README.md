# Philosophy Influence Explorer

> A multilingual, source-grounded GraphRAG application for exploring philosophical concepts, texts, and intellectual influence across Russian, English, and German.

**Philosophy Influence Explorer** is an AI research application that makes complex philosophical corpora easier to explore without concealing the evidence behind generated answers. It combines a knowledge graph, hybrid retrieval, and LLM-assisted generation to answer questions with traceable source passages and visualizable conceptual paths.

The initial corpus will focus on the intellectual trajectory from **Nicholas of Cusa** to later philosophical traditions, beginning with Cusanus, Hegel, and Semyon Frank. Later releases may incorporate Schelling, Husserl, and Heidegger.

## Why this project exists

Most RAG demonstrations are generic “chat with PDF” applications. This project is intended to demonstrate production-oriented AI engineering on a difficult multilingual humanities domain:

- Documents exist in Russian, English, German, Latin, and parallel translations.
- Historical influence must be distinguished from conceptual affinity or interpretive hypothesis.
- Each answer must be grounded in passages from the curated corpus.
- Relations in the graph must retain provenance, review status, and evidence.
- The application should be usable both by non-specialists and by researchers.

## Core capabilities

- Ask questions in Russian, English, or German.
- Search a curated multilingual philosophical corpus.
- Retrieve evidence with vector, full-text, and graph-based retrieval.
- Explain conceptual links through a knowledge graph.
- Display source passages and citations supporting each answer.
- Distinguish direct influence, quotation, critique, conceptual affinity, and unverified hypotheses.
- Refuse or qualify claims that lack evidence in the available corpus.

## Planned architecture

```text
Web client (Next.js)
        |
        v
FastAPI backend
        |
        v
LangGraph workflow
  ├── detect and normalize language
  ├── classify the question
  ├── hybrid retrieval
  ├── graph-path retrieval
  ├── evidence grading
  ├── answer generation
  └── citation and grounding verification
        |
        +-----------------------+
        |                       |
        v                       v
Neo4j graph + vector index   LLM provider
```

## Technology stack

| Area                  | Initial choice               | Purpose                                                           |
| --------------------- | ---------------------------- | ----------------------------------------------------------------- |
| Backend               | Python 3.12, FastAPI         | Typed HTTP API and application services                           |
| Dependency management | uv                           | Fast, reproducible Python environments and lockfiles              |
| Graph database        | Neo4j                        | Concepts, thinkers, works, passages, and evidence-aware relations |
| RAG orchestration     | LangChain and LangGraph      | Retrieval components and explicit stateful workflow               |
| AI models             | Provider-agnostic            | LLM generation, extraction, grading, and multilingual processing  |
| Frontend              | Next.js / React              | Trilingual exploration interface and graph visualization          |
| Quality               | pytest, Ruff, GitHub Actions | Tests, linting, and continuous integration                        |
| Deployment            | Docker Compose               | Reproducible local development and future deployment              |

## Current status

The project is in the **Neo4j integration stage**. The FastAPI server currently provides:

- `GET /` — service metadata and links.
- `GET /api/v1/health` — application health check.
- `GET /api/v1/health/database` — Neo4j connectivity health check.
- `GET /api/v1/health/database/summary` — current graph node and relationship totals.
- `GET /docs` — automatically generated interactive OpenAPI documentation.

The repository now includes a version-controlled Neo4j schema, a local Docker Compose environment, a Python Neo4j client, and a small curated seed graph. Hybrid retrieval, LangGraph orchestration, evaluation, and the frontend will be introduced incrementally.

## Quick start

### Prerequisites

- Git
- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop with Docker Compose

### 1. Clone and enter the repository

```bash
git clone [https://github.com/Yuriy2437/philosophy-influence-explorer.git](https://github.com/Yuriy2437/philosophy-influence-explorer.git)
cd philosophy-influence-explorer
```

### 2. Create local environment settings

**PowerShell (Windows):**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Before starting Neo4j, replace the placeholder value of `NEO4J_PASSWORD` in `.env` with a strong local password. Do not commit `.env`.

### 3. Install Python dependencies

```bash
uv sync --all-groups
```

### 4. Start Neo4j and apply the schema

Start the local graph database:

```bash
docker compose up -d neo4j
docker compose ps
```

Apply the version-controlled graph schema once per fresh database. In PowerShell, first load local environment values into the current terminal process:

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $name = $matches.Trim()[1]
        $value = $matches.Trim()[2]
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}
```

Then execute the schema script inside the Neo4j container:

```powershell
docker compose exec -T neo4j cypher-shell `
  -a bolt://localhost:7687 `
  -u $env:NEO4J_USERNAME `
  -p $env:NEO4J_PASSWORD `
  -d $env:NEO4J_DATABASE `
  --file /import/init/00-schema.cypher
```

The schema script is idempotent: it uses `IF NOT EXISTS`, so running it again is safe.

### 5. Seed the local demo graph

Create or update the small curated development graph:

```bash
uv run python scripts/seed_demo_graph.py
```

### 6. Run the API in development mode

```bash
uv run uvicorn philosophy_influence_explorer.main:app --reload
```

Open these addresses in a browser:

- API root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Application health check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- Neo4j connectivity check: [http://127.0.0.1:8000/api/v1/health/database](http://127.0.0.1:8000/api/v1/health/database)
- Graph summary: [http://127.0.0.1:8000/api/v1/health/database/summary](http://127.0.0.1:8000/api/v1/health/database/summary)
- Interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 7. Run quality checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

## API examples

### Application health

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "Philosophy Influence Explorer API",
  "environment": "development",
  "version": "0.1.0"
}
```

### Neo4j health

```bash
curl http://127.0.0.1:8000/api/v1/health/database
```

Expected response:

```json
{
  "status": "ok",
  "database": "neo4j"
}
```

### Graph summary

```bash
curl http://127.0.0.1:8000/api/v1/health/database/summary
```

Expected response after seeding:

```json
{
  "total_nodes": 9,
  "total_relationships": 10
}
```

The exact totals may change as the curated graph evolves.

## Local demo graph

The seed script creates a deliberately small, curated graph for local development:

- Philosophers: Nicholas of Cusa, G. W. F. Hegel, and Semyon Frank.
- Works: _De docta ignorantia_, _Wissenschaft der Logik_, and _Непостижимое_.
- Concepts: _docta ignorantia_, _coincidentia oppositorum_, and the absolute.
- Structural links: authorship and conceptual discussion.
- Two explicitly marked `candidate` conceptual relations, rather than assertions of documented historical influence.

The seed graph is not a scholarly corpus. It exists to validate the data model, Neo4j integration, API contracts, and the future retrieval workflow.

## Repository layout

```text
src/philosophy_influence_explorer/
├── api/                 # HTTP routes and API composition
├── graph/               # Neo4j client, graph queries, and curated seed data
├── core/                # Shared infrastructure and constants (planned)
├── domain/              # Domain models: passages, concepts, relations (planned)
├── ingestion/           # Document-to-graph ingestion pipeline (planned)
├── rag/                 # Retrieval, reranking, grounding, citations (planned)
├── workflows/           # LangGraph state, nodes, and routing (planned)
├── config.py            # Environment-based settings
└── main.py              # FastAPI application factory

infra/neo4j/
├── init/00-schema.cypher # Version-controlled Neo4j constraints and indexes
└── README.md             # Neo4j local development instructions

scripts/
└── seed_demo_graph.py    # Idempotent local seed-graph command

tests/                    # Unit and integration tests
```

## Data and scholarly integrity

This is not a system for asserting unverified historical influence. Every graph relation should include, where applicable:

- Relation type, such as `direct_influence`, `citation`, `critical_engagement`, or `conceptual_affinity`.
- Source passage or bibliographic evidence.
- Language and translation metadata.
- Confidence and review status.
- A distinction between curated and LLM-extracted relations.

Generated responses must cite corpus passages. If available evidence is insufficient, the application should explicitly say so.

## Development roadmap

- [x] Repository bootstrap, `uv`, FastAPI, configuration, health endpoint, and tests.
- [x] Local Neo4j environment via Docker Compose.
- [x] Version-controlled Neo4j schema and provenance-aware graph model.
- [x] Python Neo4j client, database health endpoint, and curated seed graph.
- [ ] Curated MVP corpus: Nicholas of Cusa, Hegel, Semyon Frank.
- [ ] Ingestion pipeline, passages, metadata, and provenance.
- [ ] Semantic/vector, full-text, and graph retrieval.
- [ ] Source-grounded RAG responses.
- [ ] LangGraph evidence-grade and query-rewrite workflow.
- [ ] RU/EN/DE Next.js interface with graph visualization.
- [ ] Evaluation data set, quality metrics, tracing, CI/CD, and deployed demo.

## License

This repository is intended to use the MIT License for the application code. Source texts, translations, and bibliographic metadata retain their own licenses and copyright restrictions; only legally usable materials should be added to the corpus.
