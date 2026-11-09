"""Test evaluation instruction variants without external services."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from philosophy_influence_explorer.evaluation.answer_instructions import (
    BASELINE_INSTRUCTION_ID,
    CANDIDATE_INSTRUCTION_ID,
    INSTRUCTION_IDS,
    SEMANTIC_FIDELITY_ADDITION,
    resolve_system_instruction,
)
from philosophy_influence_explorer.generation.gemini import SYSTEM_INSTRUCTION

ROOT = Path(__file__).resolve().parents[1]

BASELINE_SHA256 = (
    "da9f8bf938a147e993c38a66ff4e829adcc44effa5c0dd1452c901cbba87b4d2"
)


def test_baseline_instruction_remains_unchanged() -> None:
    baseline = resolve_system_instruction(BASELINE_INSTRUCTION_ID)

    assert baseline == SYSTEM_INSTRUCTION
    assert hashlib.sha256(baseline.encode(
        "utf-8")).hexdigest() == BASELINE_SHA256


def test_candidate_matches_exact_addition_in_committed_plan() -> None:
    plan = (
        ROOT / "docs" / "answer-quality-prompt-experiment-plan.md"
    ).read_text(encoding="utf-8")

    start = plan.index("## Candidate instruction")
    end = plan.index("## Known-set limitation", start)
    section = plan[start:end]
    quoted_lines = [
        line[2:] for line in section.splitlines() if line.startswith("> ")
    ]

    assert quoted_lines == [SEMANTIC_FIDELITY_ADDITION]
    assert resolve_system_instruction(CANDIDATE_INSTRUCTION_ID) == (
        SYSTEM_INSTRUCTION + "\n\n" + quoted_lines[0]
    )


def test_known_instruction_ids_are_explicit() -> None:
    assert INSTRUCTION_IDS == ("baseline", "semantic-fidelity-v1")


@pytest.mark.parametrize(
    "instruction_id",
    ["", "unknown", "BASELINE", " semantic-fidelity-v1"],
)
def test_unknown_instruction_id_is_rejected(instruction_id: str) -> None:
    with pytest.raises(ValueError, match="Unknown evaluation instruction"):
        resolve_system_instruction(instruction_id)
