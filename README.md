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

The project is in the **bootstrap stage**. The initial FastAPI server provides:

- `GET /` — service metadata and links.
- `GET /api/v1/health` — health-check endpoint.
- `GET /docs` — automatically generated interactive OpenAPI documentation.

Graph ingestion, Neo4j integration, retrieval, LangGraph, evaluation, and the frontend will be introduced incrementally.

## Quick start

### Prerequisites

- Git
- Python 3.12
- [uv](https://docs.astral.sh/uv/)

### 1. Clone and enter the repository

```bash
git clone https://github.com/Yuriy2437/philosophy-influence-explorer.git
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

### 3. Install Python dependencies

```bash
uv sync --all-groups
```

### 4. Run the API in development mode

```bash
uv run uvicorn philosophy_influence_explorer.main:app --reload
```

Open these addresses in a browser:

- API root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Health check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- Interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 5. Run quality checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## API example

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

## Repository layout

```text
src/philosophy_influence_explorer/
├── api/                 # HTTP routes and API composition
├── core/                # Shared infrastructure and constants (planned)
├── domain/              # Domain models: passages, concepts, relations (planned)
├── graph/               # Neo4j access and Cypher queries (planned)
├── ingestion/           # Document-to-graph ingestion pipeline (planned)
├── rag/                 # Retrieval, reranking, grounding, citations (planned)
├── workflows/           # LangGraph state, nodes, and routing (planned)
├── config.py            # Environment-based settings
└── main.py              # FastAPI application factory

tests/                   # Unit and integration tests
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
- [ ] Neo4j via Docker Compose and graph schema.
- [ ] Curated MVP corpus: Nicholas of Cusa, Hegel, Semyon Frank.
- [ ] Ingestion pipeline, passages, metadata, and provenance.
- [ ] Semantic/vector, full-text, and graph retrieval.
- [ ] Source-grounded RAG responses.
- [ ] LangGraph evidence-grade and query-rewrite workflow.
- [ ] RU/EN/DE Next.js interface with graph visualization.
- [ ] Evaluation data set, quality metrics, tracing, CI/CD, and deployed demo.

## License

This repository is intended to use the MIT License for the application code. Source texts, translations, and bibliographic metadata retain their own licenses and copyright restrictions; only legally usable materials should be added to the corpus.
