"""Shared browser harness with real assets and isolated API responses."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import Page, Route

from philosophy_influence_explorer.main import create_app


@dataclass
class SearchUI:
    """Per-test response configuration and captured browser activity."""

    payload: dict[str, Any] | None = None
    status: int = 200
    query_requests: list[dict[str, Any]] = field(default_factory=list)
    served_paths: set[str] = field(default_factory=set)
    javascript_errors: list[str] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    unexpected_requests: list[str] = field(default_factory=list)


@pytest.fixture
def search_ui(page: Page) -> Iterator[SearchUI]:
    """Serve real assets and prevent requests to external services."""
    ui = SearchUI()

    page.on("pageerror", lambda error: ui.javascript_errors.append(str(error)))
    page.on(
        "console",
        lambda message: ui.console_errors.append(message.text) if message.type == "error" else None,
    )

    with TestClient(create_app()) as client:
        assets = {
            path: client.get(path)
            for path in (
                "/search",
                "/static/search.js",
                "/static/search.css",
            )
        }

    for response in assets.values():
        assert response.status_code == 200

    def handle_request(route: Route) -> None:
        request = route.request
        url = urlsplit(request.url)
        path = url.path

        if url.netloc == "ui.test":
            if request.method == "GET" and path in assets:
                response = assets[path]
                ui.served_paths.add(path)
                route.fulfill(
                    status=200,
                    content_type=response.headers["content-type"],
                    body=response.content,
                )
                return

            if request.method == "GET" and path == "/api/v1/concepts/families":
                ui.served_paths.add(path)
                route.fulfill(json={"families": ["dialectic", "ontology"]})
                return

            if request.method == "POST" and path == "/api/v1/query" and ui.payload is not None:
                ui.query_requests.append(request.post_data_json)
                route.fulfill(status=ui.status, json=ui.payload)
                return

        ui.unexpected_requests.append(f"{request.method} {request.url}")
        route.abort()

    page.route("**/*", handle_request)

    yield ui

    assert ui.unexpected_requests == []
    assert ui.javascript_errors == []
