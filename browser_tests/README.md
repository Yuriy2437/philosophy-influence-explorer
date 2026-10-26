# Browser UI checks

These tests execute the real search-page JavaScript in Chromium.

HTML, JavaScript, and CSS are obtained from the FastAPI application
through TestClient and served to the browser through Playwright routes.
API responses use explicitly synthetic fixtures.

No running Uvicorn server, Neo4j database, embedding provider,
or deployed application is required.

## Setup

From the repository root:

```powershell
uv sync --all-groups
.\.venv\Scripts\python.exe -m playwright install chromium
```

## Run browser checks

```powershell
.\.venv\Scripts\python.exe -m pytest browser_tests -q --browser chromium
```

## Run existing unit and API checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The default pytest configuration uses testpaths = ["tests"].
Browser checks must therefore be requested explicitly.

## Check browser-test Python files

```powershell
.\.venv\Scripts\python.exe -m ruff check browser_tests
.\.venv\Scripts\python.exe -m ruff format --check browser_tests
```

## Coverage and limitations

The browser suite checks:

- Initial page loading without retrieval requests.
- Unhandled JavaScript exceptions and unexpected network requests.
- Semantic results and grouped graph paths.
- Semantic-result preservation with empty graph context.
- Empty search results.
- UI handling of prepared HTTP 429 and 503 responses.
- Query trimming and selected request filters.

The suite does not verify:

- Real HTTP-server behavior or deployed application behavior.
- Real retrieval, database connectivity, or embedding providers.
- Actual Firewall rate limiting.
- Backend enforcement of selected filters.
- Scientific accuracy or source verification.
- Responsive layout, visual appearance, or all console messages.

Browser checks are not yet integrated into CI.
