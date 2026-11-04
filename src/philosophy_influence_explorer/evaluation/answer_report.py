"""Persist evaluation reports without configuring or running generation."""

from __future__ import annotations

import json
from pathlib import Path


def save_answer_report(report: dict, destination: Path) -> None:
    """Save a JSON report to a new UTF-8 file.

    Serialize before opening the destination so serialization failures
    do not create a file. Existing destinations are never overwritten.
    Parent directories must already exist.

    This function does not validate the report schema or provide
    atomic publication. An I/O failure can leave an incomplete file.
    """
    serialized = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )

    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(serialized)
        stream.write("\n")
