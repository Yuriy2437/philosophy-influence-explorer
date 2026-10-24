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

  const searchBody = {
    q: query,
    limit: Number(limitInput.value),
    graph_limit: 20,
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
    const response = await fetch('/api/v1/query', {
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

  const passages = payload.semantic_passages;
  const paths = payload.graph_context;

  const semanticSection = createResultsSection(
    'semantic-results-heading',
    'Semantic matches'
  );

  if (passages.length === 0) {
    statusElement.textContent =
      'No passages were returned for this query and the selected filters.';

    semanticSection.append(
      createEmptyState(
        'This does not establish that the corpus contains no relevant passage. ' +
          'Try rephrasing the query or broadening the concept, language, or provenance filters.'
      )
    );
  } else {
    statusElement.textContent = `${passages.length} retrieved passage${
      passages.length === 1 ? '' : 's'
    } for “${payload.query}”. These are search matches, not a verified answer.`;

    semanticSection.append(...passages.map(createResultCard));
  }

  const graphSection = createResultsSection(
    'graph-context-heading',
    'Graph context'
  );

  const guidance = document.createElement('p');
  guidance.className = 'graph-guidance';
  guidance.textContent =
    'These paths connect passages through a shared recorded concept. ' +
    'They do not establish historical influence or provide a verified answer. ' +
    'Graph-derived passages have no vector similarity score in this section.';
  graphSection.append(guidance);

  if (paths.length === 0) {
    graphSection.append(
      createEmptyState(
        'No graph paths were returned for this query. ' +
          'This does not establish that no relevant connections exist.'
      )
    );
  } else {
    const semanticById = new Map(
      passages.map((passage) => [passage.id, passage])
    );
    const grouped = new Map();

    for (const path of paths) {
      if (!grouped.has(path.passage.id)) {
        grouped.set(path.passage.id, {
          passage: path.passage,
          paths: [],
        });
      }

      grouped.get(path.passage.id).paths.push(path);
    }

    const additionalCount = [...grouped.keys()].filter(
      (id) => !semanticById.has(id)
    ).length;

    const summary = document.createElement('p');
    summary.className = 'graph-summary';
    summary.textContent =
      `${paths.length} returned graph path(s); ` +
      `${grouped.size} distinct related passage(s), ` +
      `${additionalCount} not already shown in semantic matches. ` +
      'These are passage counts, not counts of distinct sources.';

    graphSection.append(summary);

    for (const group of grouped.values()) {
      graphSection.append(createGraphCard(group, semanticById));
    }
  }

  resultsElement.replaceChildren(semanticSection, graphSection);
}

function createResultsSection(id, headingText) {
  const section = document.createElement('section');
  section.className = 'result-section';
  section.setAttribute('aria-labelledby', id);

  const heading = document.createElement('h2');
  heading.id = id;
  heading.textContent = headingText;

  section.append(heading);
  return section;
}

function createEmptyState(message) {
  const paragraph = document.createElement('p');
  paragraph.className = 'empty-state';
  paragraph.textContent = message;
  return paragraph;
}

function createGraphCard(group, semanticById) {
  const article = createResultCard(group.passage);
  article.classList.add('graph-card');

  const origin = document.createElement('p');
  origin.className = 'graph-origin';
  origin.textContent = semanticById.has(group.passage.id)
    ? 'Already shown in semantic matches; not an additional passage.'
    : 'Additional graph-derived passage; not a separately ranked vector match.';

  const pathsHeading = document.createElement('h4');
  pathsHeading.textContent = 'Recorded concept paths';

  const pathList = document.createElement('ul');
  pathList.className = 'graph-paths';

  for (const path of group.paths) {
    const item = document.createElement('li');
    const seed = semanticById.get(path.seed_id);

    const chain = document.createElement('p');
    chain.className = 'graph-chain';
    chain.textContent =
      `${seed ? seed.citation_label || seed.id : path.seed_id} ` +
      `→ ${path.seed_edge.relation_type} → ` +
      `${path.concept.canonical_label} ` +
      `← ${path.related_edge.relation_type} ← ` +
      `${group.passage.citation_label || group.passage.id}`;

    const details = document.createElement('dl');
    details.className = 'provenance';
    details.append(
      createProvenanceRow('Seed passage ID', path.seed_id),
      createProvenanceRow('Concept ID', path.concept.id),
      createProvenanceRow('Concept family', path.concept.concept_family),
      createProvenanceRow('Seed relation ID', path.seed_edge.id),
      createProvenanceRow('Seed relation review', path.seed_edge.review_status),
      createProvenanceRow(
        'Seed relation extraction',
        path.seed_edge.extraction_method ?? 'Not recorded'
      ),
      createProvenanceRow('Related relation ID', path.related_edge.id),
      createProvenanceRow(
        'Related relation review',
        path.related_edge.review_status
      ),
      createProvenanceRow(
        'Related relation extraction',
        path.related_edge.extraction_method ?? 'Not recorded'
      )
    );

    item.append(chain, details);
    pathList.append(item);
  }

  article.append(origin, pathsHeading, pathList);
  return article;
}

function createResultCard(passage) {
  const article = document.createElement('article');
  article.className = 'result-card';

  const header = document.createElement('header');
  header.className = 'result-header';

  const title = document.createElement('h3');
  title.className = 'result-title';
  title.textContent = passage.citation_label || passage.id;

  header.append(title);

  if (Number.isFinite(passage.score)) {
    const score = document.createElement('span');
    score.className = 'score';
    score.textContent = `Vector similarity ${passage.score.toFixed(3)}`;
    score.title =
      'Vector similarity is not a probability of truth or a measure of answer completeness.';
    score.setAttribute('aria-describedby', 'similarity-guidance');

    header.append(score);
  }

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

  for (const concept of passage.concepts ?? []) {
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
