# Philosophy Influence Explorer

An early-stage, multilingual, source-grounded research application for
exploring philosophical passages and conceptual connections.

The application combines FastAPI, Neo4j, vector retrieval, explicit
LangGraph workflows, a browser search interface, and operator-only
structured answer generation.

The current implementation supports passage search and conceptual graph
context. It does not yet establish an evidence-backed historical influence
chain from Nicholas of Cusa through Hegel to Semyon Frank.

## Current capabilities

- Curated CSV ingestion for philosophers, works, passages, concepts,
  sources, and relationships.
- Vector passage retrieval with metadata filters.
- Conceptual graph expansion around retrieved passages.
- Evidence packet preparation with source provenance.
- Explicit LangGraph retrieval and answer workflows.
- Structured answer generation through a Gemini adapter.
- Structural validation of generated answers and their evidence references.
- Operator-only access to answer generation.
- A browser interface for passage search, provenance, and textual graph paths.
- Unit, API, and Chromium browser tests.
- Historical retrieval checks and fixed-evidence generation evaluation.

## Architecture

The application uses the Python package layout under
`src/philosophy_influence_explorer`.

- FastAPI provides the API and serves the browser search interface.
- Neo4j stores the curated graph and supports retrieval.
- Embedding configuration is separate from answer-generation configuration.
- LangGraph orchestrates the existing retrieval and generation services.
- Gemini provides structured answer generation through the current adapter.
- `app.py` exposes the FastAPI application as a Vercel entry point.

The browser interface is served by FastAPI. A separate Next.js frontend
is not part of the current implementation.

### Retrieval workflow

```text
validate request
  -> retrieve passages and graph context
  -> prepare evidence
```

### Answer workflow

```text
retrieve evidence
  -> generate structured draft
  -> validate answer structure and evidence references
```

These workflows are currently linear. They do not include a separate
evidence-grading stage, query rewriting, or a retrieval retry loop.

Reference validation checks that answer references belong to the supplied
evidence. It does not independently establish that every claim is
semantically supported by its cited passage.

## API and browser interface

With the default API prefix:

| Route                             | Purpose                            |
| --------------------------------- | ---------------------------------- |
| `/`                               | Service metadata                   |
| `/docs`                           | Interactive API documentation      |
| `/redoc`                          | Alternative API documentation      |
| `/openapi.json`                   | OpenAPI schema                     |
| `/search`                         | Browser passage-search interface   |
| `POST /api/v1/query`              | Retrieval-only query               |
| `POST /api/v1/answers`            | Operator-only answer generation    |
| `/api/v1/health`                  | Application health                 |
| `/api/v1/health/database`         | Neo4j connectivity health          |
| `/api/v1/health/database/summary` | Graph node and relationship totals |

The API prefix is configurable through `API_V1_PREFIX`.
The current browser code uses `/api/v1/query` directly; changing the prefix
also requires coordinating the browser configuration.

Answer generation requires:

- `GENERATION_ENABLED=true`;
- a nonempty `GENERATION_ACCESS_TOKEN`;
- the matching bearer token on the request;
- the required provider configuration.

Generation is disabled by default.

Do not embed the shared operator token in publicly served JavaScript.
The current browser search interface does not provide public answer
generation.

## Local setup

### Prerequisites

- Git.
- uv for Python version and dependency management.
- Docker Desktop with Docker Compose for local Neo4j.

The commands below use PowerShell.

### Install Python dependencies

```powershell
uv python install 3.12
uv sync --locked --all-groups --python 3.12
```

### Start the API without Neo4j

This mode is useful for inspecting the application and its API schema.
It is not a complete retrieval setup.

```powershell
$env:NEO4J_ENABLED = "false"

uv run --no-sync uvicorn philosophy_influence_explorer.main:app --reload
```

Open:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/search

Retrieval requires a configured database, imported data, and the appropriate
embedding/index setup. Serving the search page alone does not establish
that retrieval is ready.

### Start the local Neo4j service

Configure local credentials in `.env`:

```dotenv
NEO4J_ENABLED=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=replace-with-a-local-password
NEO4J_DATABASE=neo4j
```

Do not commit `.env`.

Start Neo4j:

```powershell
docker compose up -d neo4j
```

If `NEO4J_ENABLED` was set to `false` in this PowerShell session,
remove that process-level override before starting the application:

```powershell
Remove-Item Env:NEO4J_ENABLED -ErrorAction SilentlyContinue
```

Then start the API:

```powershell
uv run --no-sync uvicorn philosophy_influence_explorer.main:app --reload
```

The Compose service exposes Neo4j Browser on port 7474 and Bolt on port 7687.
It persists database data in Docker volumes.

The Compose file mounts `infra/neo4j/init` into the container. Starting the
container should not be treated as proof that schema creation, corpus
ingestion, embeddings, or vector-index preparation have completed.

### Configuration boundaries

Application settings load `.env` through Pydantic Settings.

The evaluated generation CLI uses process environment variables directly.
Do not assume that placing a provider key in `.env` makes it available to
every standalone command.

The current answer endpoint explicitly uses the Gemini generator and
`GENERATION_MODEL`. The generic `LLM_PROVIDER` setting should not be
interpreted as a working provider switch for this endpoint.

Provider defaults are configuration values, not guarantees of model
availability, quota, or free usage. Check those constraints before making
new live calls.

## Tests and CI

Run unit and API tests without Neo4j:

```powershell
$env:NEO4J_ENABLED = "false"
uv run --no-sync python -m pytest tests -q
```

Install Chromium and run browser tests:

```powershell
uv run --no-sync python -m playwright install chromium
uv run --no-sync python -m pytest browser_tests -q --browser chromium
```

Check browser-test lint and formatting:

```powershell
uv run --no-sync python -m ruff check browser_tests
uv run --no-sync python -m ruff format --check browser_tests
```

The GitHub Actions test workflow has separate unit/API and Chromium jobs.
It uses Python 3.12, locked dependencies, and `NEO4J_ENABLED=false`.

This workflow does not provision a live Neo4j database, explicitly run a
live Gemini evaluation, or deploy the application.

## Corpus and evaluation limitations

The curated data includes Nicholas of Cusa, Hegel, Semyon Frank, Kant,
and John Stuart Mill.

The current relationships describe authorship, passage membership,
concept discussion, and selected conceptual relationships. They do not
yet encode a supported cross-author historical influence chain.

Bibliographic notes and editorial summaries must remain distinguishable
from verbatim primary-source passages.

Review status and licensing status are separate. Some source and rights
checks remain unresolved. A `reviewed` record does not by itself establish
permission for every publication or reuse scenario.

`data/evaluation/semantic-search-v1.json` contains 12 historical retrieval
checks: eight English queries and four Russian queries. It contains no
German-language queries.

The suite explicitly documents that it is not an independent held-out
benchmark. Historical outcomes should not be presented as a fresh run.

Fixed-evidence generation evaluation and retrieval evaluation cover
different parts of the system. Neither alone establishes end-to-end answer
quality or author approval of scientific criteria.

## Deployment and observability

`app.py` provides a Vercel application entry point. Its presence does not
by itself establish that the current complete workflow has passed a fresh
deployment acceptance test.

LangSmith-related settings exist, but operational tracing has not been
confirmed by this audit.

## Further documentation

- [Local Neo4j setup](infra/neo4j/README.md)
- [Semantic search evaluation](docs/semantic-search-evaluation.md)
- [LangGraph retrieval workflow](docs/langgraph-retrieval-workflow.md)

These documents cover specific components and historical verification.
For the current overall implementation status, use this README and
the remaining roadmap.

## Next steps

See [the roadmap](docs/roadmap.md) for the remaining scope and acceptance
criteria.

The next substantive task is to inspect the Frank materials and define
which questions the core corpus can responsibly support, before further
prompt experiments.

## Licensing

Application code and corpus materials have separate licensing requirements.

The project metadata declares the MIT License for application code.
Source texts, translations, and bibliographic materials retain their own
licenses and copyright restrictions.

Unresolved source and rights checks are recorded in the curated data.
Do not treat the application code's license as permission to redistribute
all corpus materials.
