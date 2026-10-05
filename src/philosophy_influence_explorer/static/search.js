'use strict';

const form = document.querySelector('#search-form');
const queryInput = document.querySelector('#query');
const conceptFamilyInput = document.querySelector('#concept-family');
const languageInput = document.querySelector('#language');
const limitInput = document.querySelector('#limit');
const statusElement = document.querySelector('#status');
const resultsElement = document.querySelector('#results');

void loadConceptFamilies();

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const query = queryInput.value.trim();

  if (!query) {
    renderError('Enter a semantic query before searching.');
    return;
  }

  const searchParameters = new URLSearchParams({
    q: query,
    limit: limitInput.value,
  });

  const searchBody = {
    q: query,
    limit: Number(limitInput.value),
  };

  if (conceptFamilyInput.value) {
    searchBody.concept_family = conceptFamilyInput.value;
  }

  if (languageInput.value) {
    searchBody.language = languageInput.value;
  }

  const materialKind = form.elements.material_kind.value;

  if (materialKind === 'primary') {
    searchBody.is_verbatim = true;
    searchBody.is_editorial = false;
  }

  if (materialKind === 'editorial') {
    searchBody.is_verbatim = false;
    searchBody.is_editorial = true;
  }

  setLoadingState();

  try {
    const response = await fetch('/api/v1/passages/search', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(searchBody),
    });

    const payload = await response.json();

    if (response.status === 429) {
      throw new Error(
        'Search is temporarily rate-limited. Please wait a moment and try again.'
      );
    }

    if (!response.ok) {
      throw new Error(
        payload.detail || 'The semantic search request could not be completed.'
      );
    }

    renderResults(payload);
  } catch (error) {
    renderError(error.message);
  }
});

function setLoadingState() {
  statusElement.className = 'status';
  statusElement.textContent = 'Searching the curated corpus…';
  resultsElement.replaceChildren();
}

function renderError(message) {
  statusElement.className = 'status error';
  statusElement.textContent = `Search unavailable: ${message}`;
  resultsElement.replaceChildren();
}

function renderResults(payload) {
  statusElement.className = 'status';

  if (payload.count === 0) {
    statusElement.textContent = 'No passages matched the selected filters.';
    const emptyState = document.createElement('p');
    emptyState.className = 'empty-state';
    emptyState.textContent =
      'Try a broader query or remove one of the concept, language, or provenance filters.';
    resultsElement.replaceChildren(emptyState);
    return;
  }

  statusElement.textContent = `${payload.count} result${
    payload.count === 1 ? '' : 's'
  } for “${payload.query}”.`;

  const cards = payload.results.map(createResultCard);
  resultsElement.replaceChildren(...cards);
}

function createResultCard(passage) {
  const article = document.createElement('article');
  article.className = 'result-card';

  const header = document.createElement('header');
  header.className = 'result-header';

  const title = document.createElement('h3');
  title.className = 'result-title';
  title.textContent = passage.citation_label || passage.id;

  const score = document.createElement('span');
  score.className = 'score';
  score.textContent = `Similarity ${passage.score.toFixed(3)}`;

  header.append(title, score);

  const badges = document.createElement('div');
  badges.className = 'badges';
  badges.append(
    createBadge(
      passage.is_verbatim ? 'Primary quotation' : 'Non-verbatim',
      passage.is_verbatim ? 'primary' : 'editorial'
    ),
    createBadge(
      passage.is_editorial ? 'Editorial material' : 'Non-editorial',
      passage.is_editorial ? 'editorial' : 'primary'
    ),
    createBadge(passage.language.toUpperCase(), 'language'),
    createBadge(
      `Review: ${passage.review_status}`,
      passage.review_status === 'candidate' ? 'candidate' : 'reviewed'
    )
  );

  const text = document.createElement('p');
  text.className = 'passage-text';
  text.textContent = passage.text;

  const concepts = document.createElement('div');
  concepts.className = 'concepts';

  for (const concept of passage.concepts) {
    const conceptBadge = document.createElement('span');
    conceptBadge.className = 'concept-badge';
    conceptBadge.textContent = `${concept.concept_family} · ${concept.canonical_label}`;
    concepts.append(conceptBadge);
  }

  const provenance = document.createElement('dl');
  provenance.className = 'provenance';
  provenance.append(
    createProvenanceRow('Citation', passage.citation_label),
    createProvenanceRow('Work', passage.work_id),
    createProvenanceRow('Source', passage.source_id),
    createProvenanceRow('Passage ID', passage.id),
    createProvenanceRow('Text kind', passage.text_kind)
  );

  article.append(header, badges, text, concepts, provenance);
  return article;
}

function createBadge(text, variant) {
  const badge = document.createElement('span');
  badge.className = `badge ${variant}`;
  badge.textContent = text;
  return badge;
}

function createProvenanceRow(label, value) {
  const row = document.createElement('div');
  row.className = 'provenance-row';

  const term = document.createElement('dt');
  term.textContent = `${label}: `;

  const description = document.createElement('dd');
  description.textContent = value;

  row.append(term, description);
  return row;
}

async function loadConceptFamilies() {
  const previousValue = conceptFamilyInput.value;

  try {
    const response = await fetch('/api/v1/concepts/families', {
      headers: { Accept: 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();

    if (
      !Array.isArray(payload.families) ||
      !payload.families.every(
        (family) => typeof family === 'string' && family.length > 0
      )
    ) {
      throw new Error('Invalid concept families response');
    }

    const anyOption = new Option('Any concept family', '');
    const familyOptions = payload.families.map(
      (family) => new Option(family.replaceAll('_', ' '), family)
    );

    conceptFamilyInput.replaceChildren(anyOption, ...familyOptions);

    if (payload.families.includes(previousValue)) {
      conceptFamilyInput.value = previousValue;
    }
  } catch (error) {
    console.error('Could not load concept families:', error);
    // Оставляем существующие options: поиск продолжит работать.
  }
}
