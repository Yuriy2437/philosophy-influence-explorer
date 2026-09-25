"""Minimal browser UI for concept-aware semantic Passage search."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["search UI"])

_SEARCH_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Philosophy Influence Explorer — Semantic Search</title>
  <link rel="stylesheet" href="/static/search.css">
</head>
<body>
  <main class="page-shell">
    <header class="hero">
      <p class="eyebrow">Philosophy Influence Explorer</p>
      <h1>Concept-aware semantic search</h1>
      <p class="hero-copy">
        Search the curated philosophical corpus by meaning, language,
        provenance, and graph concepts.
      </p>
    </header>

    <section class="search-panel" aria-labelledby="search-heading">
      <h2 id="search-heading">Search passages</h2>

      <form id="search-form">
        <label for="query">Semantic query</label>
        <textarea
          id="query"
          name="q"
          rows="3"
          required
          placeholder="For example: being, nothing, and becoming in Hegel"
        ></textarea>

        <div class="filter-grid">
          <div>
            <label for="concept-family">Concept family</label>
            <select id="concept-family" name="concept_family">
              <option value="">Any concept family</option>
              <option value="dialectic">Dialectic</option>
              <option value="epistemology">Epistemology</option>
              <option value="metaphysics">Metaphysics</option>
              <option value="ontology">Ontology</option>
            </select>
          </div>

          <div>
            <label for="language">Language</label>
            <select id="language" name="language">
              <option value="">Any language</option>
              <option value="en">English</option>
              <option value="ru">Russian</option>
              <option value="de">German</option>
              <option value="la">Latin</option>
            </select>
          </div>

          <div>
            <label for="limit">Maximum results</label>
            <select id="limit" name="limit">
              <option value="3">3</option>
              <option value="5" selected>5</option>
              <option value="10">10</option>
              <option value="20">20</option>
            </select>
          </div>
        </div>

        <fieldset class="provenance-filters">
          <legend>Provenance filter</legend>

          <label class="radio-option">
            <input type="radio" name="material_kind" value="" checked>
            Any material
          </label>

          <label class="radio-option">
            <input type="radio" name="material_kind" value="primary">
            Primary quotations only
          </label>

          <label class="radio-option">
            <input type="radio" name="material_kind" value="editorial">
            Editorial material only
          </label>
        </fieldset>

        <button type="submit">Search corpus</button>
      </form>
    </section>

    <section
      id="status"
      class="status"
      aria-live="polite"
    ></section>

    <section
      id="results"
      class="results"
      aria-live="polite"
      aria-label="Search results"
    ></section>
  </main>

  <script src="/static/search.js" defer></script>
</body>
</html>
"""


@router.get(
    "/search",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def search_page() -> HTMLResponse:
    """Return the browser UI without invoking retrieval infrastructure."""
    return HTMLResponse(content=_SEARCH_PAGE)
