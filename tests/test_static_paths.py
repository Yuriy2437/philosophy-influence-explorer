"""Tests for packaged static asset paths."""

from philosophy_influence_explorer.main import STATIC_DIR


def test_static_directory_contains_search_assets() -> None:
    """Static assets must be discoverable from the installed package path."""
    assert STATIC_DIR.is_dir()
    assert (STATIC_DIR / "search.css").is_file()
    assert (STATIC_DIR / "search.js").is_file()
